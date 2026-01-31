#!/usr/bin/env python3
"""Kalshi API client for fetching and displaying prediction markets."""

import asyncio
import logging
import time
import httpx
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Config:
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    TIMEOUT_SECONDS = 30.0
    MAX_API_LIMIT = 1000
    DEFAULT_PAGE_SIZE = 200
    SECONDS_IN_24H = 86400
    ARENA_MIN_VOLUME = 10_000
    DEFAULT_FETCH_LIMIT = 10000
    MAX_CONNECTIONS = 100
    MAX_KEEPALIVE_CONNECTIONS = 20


@dataclass
class Market:
    """Represents a Kalshi prediction market."""
    ticker: str
    event_ticker: str
    title: str
    yes_sub_title: str
    yes_bid: int          # Price in cents (0-100)
    no_bid: int           # Price in cents (0-100)
    volume: int           # Contracts traded
    close_time: str       # ISO 8601 timestamp
    status: str
    category: str = "N/A"

    @property
    def formatted_close_time(self) -> str:
        if not self.close_time:
            return "N/A"
        try:
            dt = datetime.fromisoformat(self.close_time.replace('Z', '+00:00'))
            return dt.strftime("%b %d, %I:%M%p")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse close_time '{self.close_time}': {e}")
            return self.close_time[:16] if len(self.close_time) >= 16 else self.close_time

    @property
    def formatted_volume(self) -> str:
        if self.volume >= 1_000_000:
            return f"{self.volume / 1_000_000:.1f}M"
        elif self.volume >= 1_000:
            return f"{self.volume / 1_000:.1f}K"
        return f"{self.volume}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Market':
        return cls(
            ticker=data.get('ticker', ''),
            event_ticker=data.get('event_ticker', 'UNKNOWN'),
            title=data.get('title', 'N/A'),
            yes_sub_title=data.get('yes_sub_title', data.get('ticker', 'N/A')),
            yes_bid=data.get('yes_bid', 0),
            no_bid=data.get('no_bid', 0),
            volume=data.get('volume', 0),
            close_time=data.get('close_time', ''),
            status=data.get('status', 'unknown'),
            category=data.get('category', 'N/A')
        )


class KalshiAPI:
    """Async client for the Kalshi prediction market API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        limits = httpx.Limits(
            max_connections=Config.MAX_CONNECTIONS,
            max_keepalive_connections=Config.MAX_KEEPALIVE_CONNECTIONS
        )
        self.client = httpx.AsyncClient(
            base_url=Config.BASE_URL,
            headers=headers,
            timeout=Config.TIMEOUT_SECONDS,
            limits=limits
        )
        logger.info("Initialized KalshiAPI client")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        logger.info("Closed KalshiAPI client")

    async def _paginate(
        self,
        endpoint: str,
        params: Dict[str, Any],
        limit: int,
        result_key: str = "events"
    ) -> List[Dict[str, Any]]:
        """Paginate through API results with automatic retry on transient failures."""
        all_items = []
        cursor = None
        retry_count = 0
        max_retries = 3

        while True:
            current_params = params.copy()
            if cursor:
                current_params["cursor"] = cursor

            try:
                response = await self.client.get(endpoint, params=current_params)
                response.raise_for_status()
                retry_count = 0

                data = response.json()
                items = data.get(result_key, [])
                all_items.extend(items)
                logger.debug(f"Fetched {len(items)} items from {endpoint} (total: {len(all_items)})")

                cursor = data.get("cursor")
                if not cursor or len(all_items) >= limit:
                    break

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning("Rate limit exceeded, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error("Max retries exceeded for rate limiting")
                        break
                    continue
                elif e.response.status_code >= 500:
                    logger.error(f"Server error {e.response.status_code}: {e.response.text}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error("Max retries exceeded for server errors")
                        break
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                    break

            except httpx.TimeoutException:
                logger.warning("Request timeout, retrying...")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Max retries exceeded for timeouts")
                    break
                await asyncio.sleep(2)
                continue

            except httpx.RequestError as e:
                logger.error(f"Network error: {e}")
                break

        return all_items[:limit]

    async def get_events(
        self,
        limit: int = 100,
        status: str = "open",
        with_nested_markets: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch events from Kalshi API."""
        params = {
            "limit": min(limit, Config.DEFAULT_PAGE_SIZE),
            "status": status,
            "with_nested_markets": str(with_nested_markets).lower(),
        }
        logger.info(f"Fetching events with status={status}, limit={limit}")
        return await self._paginate("events", params, limit, "events")

    async def get_markets_for_event(self, event_ticker: str) -> List[Dict[str, Any]]:
        """Fetch markets for a specific event."""
        logger.info(f"Fetching markets for event: {event_ticker}")
        try:
            response = await self.client.get(f"events/{event_ticker}/markets")
            response.raise_for_status()
            data = response.json()
            markets = data.get("markets", [])
            logger.info(f"Retrieved {len(markets)} markets for event {event_ticker}")
            return markets
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching markets for event {event_ticker}: {e.response.status_code}")
            return []

    async def get_markets(self, limit: int = 10, status: str = "open") -> List[Dict[str, Any]]:
        """Fetch all markets with prices."""
        params = {
            "limit": min(limit, Config.DEFAULT_PAGE_SIZE),
            "status": status,
        }
        logger.info(f"Fetching markets with status={status}, limit={limit}")
        return await self._paginate("markets", params, limit, "markets")

    async def get_markets_closing_within_24h(self, limit: int = 1000, status: str = "open") -> List[Dict[str, Any]]:
        """Fetch markets closing within the next 24 hours."""
        current_time = int(time.time())
        time_24h = current_time + Config.SECONDS_IN_24H
        params = {
            "limit": min(limit, Config.MAX_API_LIMIT),
            "status": status,
            "min_close_ts": current_time,
            "max_close_ts": time_24h,
        }
        logger.info(f"Fetching markets closing within 24h (limit={limit})")
        return await self._paginate("markets", params, limit, "markets")

    async def get_markets_closing_in_range(
        self,
        min_days: int = 4,
        max_days: int = 10,
        limit: int = 10000,
        status: str = "open"
    ) -> List[Dict[str, Any]]:
        """Fetch markets closing within a specified day range."""
        current_time = int(time.time())
        min_close_ts = current_time + (min_days * 86400)
        max_close_ts = current_time + (max_days * 86400)
        params = {
            "limit": min(limit, Config.MAX_API_LIMIT),
            "status": status,
            "min_close_ts": min_close_ts,
            "max_close_ts": max_close_ts,
        }
        logger.info(f"Fetching markets closing in {min_days}-{max_days} days (limit={limit})")
        return await self._paginate("markets", params, limit, "markets")


def group_markets_by_event(markets: List[Market]) -> Dict[str, Dict[str, Any]]:
    """Group markets by their parent event."""
    events = defaultdict(lambda: {'title': '', 'category': '', 'markets': []})
    for market in markets:
        event = events[market.event_ticker]
        if not event['title']:
            event['title'] = market.title
            event['category'] = market.category
        event['markets'].append(market)
    return dict(events)


def display_markets(events_dict: Dict[str, Dict[str, Any]]) -> None:
    """Display formatted market data grouped by event."""
    for i, (event_ticker, event_data) in enumerate(events_dict.items(), 1):
        title = event_data['title']
        category = event_data['category']
        markets = event_data['markets']

        print(f"\n{'='*100}")
        print(f"📌 [{i}] {title}")
        print(f"   Category: {category} | Markets: {len(markets)}")
        print(f"{'-'*100}")
        print(f"   {'OUTCOME':<40} {'YES¢':<8} {'NO¢':<8} {'CONTRACTS':<12} {'CLOSES':<15}")
        print(f"   {'-'*90}")

        for market in markets[:10]:
            outcome = market.yes_sub_title[:38]
            print(f"   {outcome:<40} {market.yes_bid:<8} {market.no_bid:<8} "
                  f"{market.formatted_volume:<12} {market.formatted_close_time:<15}")

        if len(markets) > 10:
            print(f"   ... and {len(markets) - 10} more outcomes")


async def main():
    """Fetch and display Kalshi markets closing in 4-10 days with 10K+ volume."""
    min_days = 4
    max_days = 10
    min_volume = 10_000

    print(f"🎯 Kalshi Markets Closing in {min_days}-{max_days} Days (Volume > {min_volume:,})\n")

    async with KalshiAPI() as api:
        logger.info("Starting market fetch...")
        all_markets_data = await api.get_markets_closing_in_range(
            min_days=min_days,
            max_days=max_days,
            limit=Config.DEFAULT_FETCH_LIMIT,
            status="open"
        )

        all_markets = [Market.from_dict(m) for m in all_markets_data]
        filtered_markets = [m for m in all_markets if m.volume >= min_volume]

        print(f"📊 Found {len(all_markets)} markets total")
        print(f"✅ {len(filtered_markets)} markets with {min_volume:,}+ contracts traded")
        print(f"🚫 Filtered out {len(all_markets) - len(filtered_markets)} markets with low volume\n")
        logger.info(f"Filtered to {len(filtered_markets)} markets with sufficient volume")

        events_dict = group_markets_by_event(filtered_markets)
        display_markets(events_dict)

    print(f"\n{'='*100}")
    print(f"\n💡 Prices in cents (0-100). YES 45¢ = 45% probability = $0.45 cost per share")
    print(f"📊 Volume shown in contracts traded (YES and NO count separately)")
    print(f"⏰ All markets shown close within {min_days}-{max_days} days")
    logger.info("Script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
