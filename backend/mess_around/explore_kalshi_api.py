#!/usr/bin/env python3
"""
Simplified Kalshi API script to fetch and display events.
Run with: python backend/mess_around/explore_kalshi_api.py
"""

import asyncio
import httpx
from typing import List, Dict, Any
import json
import time


class KalshiAPI:
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def get_events(
        self,
        limit: int = 100,
        status: str = "open",
        with_nested_markets: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch events from Kalshi API"""
        all_events = []
        cursor = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "limit": min(limit, 200),
                    "status": status,
                    "with_nested_markets": str(with_nested_markets).lower(),
                }
                if cursor:
                    params["cursor"] = cursor

                response = await client.get(
                    f"{self.BASE_URL}/events",
                    headers=self.headers,
                    params=params
                )

                if response.status_code != 200:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    break

                data = response.json()
                events = data.get("events", [])
                all_events.extend(events)

                cursor = data.get("cursor")
                if not cursor or len(all_events) >= limit:
                    break

        return all_events[:limit]

    async def get_markets_for_event(self, event_ticker: str) -> List[Dict[str, Any]]:
        """Fetch markets (with prices) for a specific event"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/events/{event_ticker}/markets",
                headers=self.headers
            )

            if response.status_code != 200:
                print(f"❌ Error fetching markets: {response.status_code}")
                return []

            data = response.json()
            return data.get("markets", [])

    async def get_markets(self, limit: int = 10, status: str = "open") -> List[Dict[str, Any]]:
        """Fetch all markets with prices"""
        all_markets = []
        cursor = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "limit": min(limit, 200),
                    "status": status,
                }
                if cursor:
                    params["cursor"] = cursor

                response = await client.get(
                    f"{self.BASE_URL}/markets",
                    headers=self.headers,
                    params=params
                )

                if response.status_code != 200:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    break

                data = response.json()
                markets = data.get("markets", [])
                all_markets.extend(markets)

                cursor = data.get("cursor")
                if not cursor or len(all_markets) >= limit:
                    break

        return all_markets[:limit]

    async def get_markets_closing_within_24h(
        self,
        limit: int = 1000,
        status: str = "open"
    ) -> List[Dict[str, Any]]:
        """Fetch markets closing within 24 hours"""
        all_markets = []
        cursor = None

        # Calculate time range
        current_time = int(time.time())
        time_24h = current_time + 86400  # 24 hours = 86400 seconds

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "limit": min(limit, 1000),  # API max is 1000
                    "status": status,
                    "min_close_ts": current_time,
                    "max_close_ts": time_24h,
                }
                if cursor:
                    params["cursor"] = cursor

                response = await client.get(
                    f"{self.BASE_URL}/markets",
                    headers=self.headers,
                    params=params
                )

                if response.status_code != 200:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    break

                data = response.json()
                markets = data.get("markets", [])
                all_markets.extend(markets)

                cursor = data.get("cursor")
                if not cursor or len(all_markets) >= limit:
                    break

        return all_markets[:limit]


def format_close_time(close_time: str) -> str:
    """Format ISO timestamp to readable datetime with hours"""
    if not close_time:
        return "N/A"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
        # Include time for 24h markets
        return dt.strftime("%b %d, %I:%M%p")
    except:
        return close_time[:16]


async def main():
    print("🎯 Kalshi Markets Closing Within 24 Hours\n")

    api = KalshiAPI()

    # Fetch markets closing within 24 hours
    all_markets = await api.get_markets_closing_within_24h(limit=10000, status="open")

    # Filter out markets with low volume
    # Volume is measured in number of contracts traded (YES and NO count separately)
    ARENA_MIN_VOLUME = 25_000  # ~$25K-50K in dollar volume - good for AI arena display
    filtered_markets = [m for m in all_markets if m.get('volume', 0) >= ARENA_MIN_VOLUME]

    print(f"📊 Found {len(all_markets)} markets total")
    print(f"✅ {len(filtered_markets)} markets with {ARENA_MIN_VOLUME:,}+ contracts traded")
    print(f"🚫 Filtered out {len(all_markets) - len(filtered_markets)} markets with low volume\n")

    # Group markets by event for better organization
    events_dict = {}
    for market in filtered_markets:
        event_ticker = market.get('event_ticker', 'UNKNOWN')
        if event_ticker not in events_dict:
            events_dict[event_ticker] = {
                'title': market.get('title', 'N/A'),
                'category': market.get('category', 'N/A'),
                'markets': []
            }
        events_dict[event_ticker]['markets'].append(market)

    # Display grouped by event
    for i, (event_ticker, event_data) in enumerate(events_dict.items(), 1):
        title = event_data['title']
        category = event_data['category']
        markets = event_data['markets']

        print(f"\n{'='*100}")
        print(f"📌 [{i}] {title}")
        print(f"   Category: {category} | Markets: {len(markets)}")
        print(f"-"*100)

        print(f"   {'OUTCOME':<40} {'YES¢':<8} {'NO¢':<8} {'CONTRACTS':<12} {'CLOSES':<15}")
        print(f"   {'-'*90}")

        for market in markets[:10]:  # Show up to 10 outcomes per event
            # Use yes_sub_title for both single and multi-outcome markets
            outcome = market.get('yes_sub_title', market.get('ticker', 'N/A'))[:38]
            yes_bid = market.get('yes_bid', 0)
            no_bid = market.get('no_bid', 0)
            volume = market.get('volume', 0)
            close_time = format_close_time(market.get('close_time', ''))

            # Format volume (in contracts, not dollars)
            if volume >= 1_000_000:
                vol_str = f"{volume/1_000_000:.1f}M"
            elif volume >= 1_000:
                vol_str = f"{volume/1_000:.1f}K"
            else:
                vol_str = f"{volume}"

            print(f"   {outcome:<40} {yes_bid:<8} {no_bid:<8} {vol_str:<12} {close_time:<15}")

        if len(markets) > 10:
            print(f"   ... and {len(markets) - 10} more outcomes")

    print(f"\n{'='*100}")
    print(f"\n💡 Prices in cents (0-100). YES 45¢ = 45% probability = $0.45 cost per share")
    print(f"📊 Volume shown in contracts traded (YES and NO count separately)")
    print(f"⏰ All markets shown close within the next 24 hours")


if __name__ == "__main__":
    asyncio.run(main())
