"""Kalshi API integration service."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class KalshiService:
    """
    Integration with Kalshi prediction market API.
    Uses public endpoints for market data retrieval.
    """

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_events_closing_today(self) -> list[dict[str, Any]]:
        """
        Fetch events from Kalshi where betting closes today.
        Filters for markets with status='open' and close_time within 24 hours.
        """
        now = datetime.now(timezone.utc)
        end_of_day = now.replace(hour=23, minute=59, second=59)

        try:
            response = await self.client.get(
                "/markets",
                params={
                    "status": "open",
                    "limit": 200,
                },
            )
            response.raise_for_status()
            data = response.json()

            markets = data.get("markets", [])
            closing_today = []

            for market in markets:
                close_time_str = market.get("close_time")
                if not close_time_str:
                    continue

                close_time = datetime.fromisoformat(
                    close_time_str.replace("Z", "+00:00")
                )

                # Check if closing within 24 hours
                if now <= close_time <= end_of_day + timedelta(hours=24):
                    closing_today.append(market)

            logger.info(f"Found {len(closing_today)} events closing today")
            return closing_today

        except httpx.HTTPError as e:
            logger.error(f"Error fetching events from Kalshi: {e}")
            return []

    async def get_market_details(self, market_ticker: str) -> Optional[dict[str, Any]]:
        """Fetch detailed market data including current price and volume."""
        try:
            response = await self.client.get(f"/markets/{market_ticker}")
            response.raise_for_status()
            return response.json().get("market")
        except httpx.HTTPError as e:
            logger.error(f"Error fetching market {market_ticker}: {e}")
            return None

    async def get_market_price(self, market_ticker: str) -> Optional[Decimal]:
        """Get current YES price for a market."""
        market = await self.get_market_details(market_ticker)
        if market:
            # Kalshi returns price in cents (0-100)
            yes_price = market.get("yes_bid", market.get("last_price", 50))
            return Decimal(str(yes_price)) / 100
        return None

    async def get_settlement_result(self, market_ticker: str) -> Optional[str]:
        """
        Check if market is settled and return outcome.
        Returns 'YES', 'NO', or None if not settled.
        """
        market = await self.get_market_details(market_ticker)
        if market:
            result = market.get("result")
            if result == "yes":
                return "YES"
            elif result == "no":
                return "NO"
        return None

    async def get_event_details(self, event_ticker: str) -> Optional[dict[str, Any]]:
        """Fetch event details (contains multiple markets)."""
        try:
            response = await self.client.get(f"/events/{event_ticker}")
            response.raise_for_status()
            return response.json().get("event")
        except httpx.HTTPError as e:
            logger.error(f"Error fetching event {event_ticker}: {e}")
            return None

    async def search_markets(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search for markets by query string."""
        try:
            response = await self.client.get(
                "/markets",
                params={
                    "status": "open",
                    "limit": limit,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Filter by query (Kalshi API doesn't have search)
            markets = data.get("markets", [])
            query_lower = query.lower()
            filtered = [
                m for m in markets
                if query_lower in m.get("title", "").lower()
                or query_lower in m.get("subtitle", "").lower()
            ]

            return filtered[:limit]

        except httpx.HTTPError as e:
            logger.error(f"Error searching markets: {e}")
            return []


# Singleton instance
kalshi_service = KalshiService()
