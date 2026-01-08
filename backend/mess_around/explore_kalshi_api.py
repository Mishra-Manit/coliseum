#!/usr/bin/env python3
"""
Simple Kalshi API exploration script.
Purpose: Understand event structure, filtering, and data format before building pipeline.

Run with: python backend/mess_around/explore_kalshi_api.py
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class KalshiExplorer:
    """
    Based on Kalshi API docs: https://trading-api.readme.io/reference/getting-started
    """

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def get_markets(
        self,
        limit: int = 100,
        status: str = "open",
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from Kalshi API with pagination support.

        Markets are the actual tradeable contracts (unlike events which are containers).

        Args:
            limit: Number of markets per page (max 200)
            status: Market status filter (open, closed, settled)
            **filters: Additional query parameters

        Returns:
            List of market dictionaries
        """
        all_markets = []
        cursor = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "limit": min(limit, 200),  # Kalshi max is 200
                    "status": status,
                    **filters
                }
                if cursor:
                    params["cursor"] = cursor

                print(f"📡 Fetching markets (cursor: {cursor or 'initial'})...")

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

                print(f"   ✓ Received {len(markets)} markets (total: {len(all_markets)})")

                # Check if there are more pages
                cursor = data.get("cursor")
                if not cursor or len(all_markets) >= limit:
                    break

        return all_markets[:limit]

    async def get_events(
        self,
        limit: int = 100,
        status: str = "open",
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from Kalshi API with pagination support.

        NOTE: Events are containers. For trading data, use get_markets() instead.

        Args:
            limit: Number of events per page (max 200)
            status: Event status filter (open, closed, settled)
            **filters: Additional query parameters

        Returns:
            List of event dictionaries
        """
        all_events = []
        cursor = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "limit": min(limit, 200),  # Kalshi max is 200
                    "status": status,
                    **filters
                }
                if cursor:
                    params["cursor"] = cursor

                print(f"📡 Fetching events (cursor: {cursor or 'initial'})...")

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

                print(f"   ✓ Received {len(events)} events (total: {len(all_events)})")

                # Check if there are more pages
                cursor = data.get("cursor")
                if not cursor or len(all_events) >= limit:
                    break

        return all_events[:limit]

    async def get_markets_for_event(self, event_ticker: str) -> List[Dict[str, Any]]:
        """
        Fetch all markets for a specific event.
        An event can have multiple markets (e.g., different outcomes).
        """
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

    def print_event_summary(self, event: Dict[str, Any], index: int = None):
        """Print a nicely formatted event summary."""
        prefix = f"{index}. " if index else ""

        ticker = event.get("ticker", "N/A")
        title = event.get("title", "No title")
        category = event.get("category", "Unknown")
        series_ticker = event.get("series_ticker", "N/A")

        # Parse close time
        close_time_str = event.get("close_time", "N/A")
        if close_time_str != "N/A":
            try:
                close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                hours_until_close = (close_time - datetime.now(close_time.tzinfo)).total_seconds() / 3600
                close_display = f"{close_time.strftime('%Y-%m-%d %H:%M UTC')} ({hours_until_close:.1f}h)"
            except:
                close_display = close_time_str
        else:
            close_display = "N/A"

        print(f"""
{prefix}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Ticker: {ticker}
  Title: {title}
  Category: {category}
  Series: {series_ticker}
  Closes: {close_display}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")

    def print_market_summary(self, market: Dict[str, Any], index: int = None):
        """Print a nicely formatted market summary."""
        prefix = f"  [{index}] " if index else "  "

        ticker = market.get("ticker", "N/A")
        subtitle = market.get("subtitle", "")
        yes_bid = market.get("yes_bid", 0) / 100  # Convert cents to price
        yes_ask = market.get("yes_ask", 0) / 100
        volume = market.get("volume", 0)
        open_interest = market.get("open_interest", 0)

        print(f"""{prefix}Market: {ticker}
     Question: {subtitle}
     YES Price: {yes_bid:.2%} bid / {yes_ask:.2%} ask
     Volume: ${volume:,}
     Open Interest: ${open_interest:,}""")

    def filter_binary_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter for SIMPLE binary YES/NO markets only (as per DESIGN.md requirement).

        Excludes:
        - Multivariate markets (parlays with multiple legs)
        - Markets without pricing data
        """
        binary_markets = []
        for market in markets:
            # Skip multivariate/parlay markets (they have mve_selected_legs)
            if "mve_selected_legs" in market and market["mve_selected_legs"]:
                continue

            # Must be explicitly marked as binary
            if market.get("market_type") != "binary":
                continue

            # Must have YES/NO pricing data
            if "yes_ask" not in market or "yes_bid" not in market:
                continue

            binary_markets.append(market)

        return binary_markets

    def filter_closing_soon(
        self,
        events: List[Dict[str, Any]],
        min_hours: int = 0,
        max_hours: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Filter events closing within specified time window.

        Args:
            events: List of events
            min_hours: Minimum hours until close (default: 0 = now)
            max_hours: Maximum hours until close (default: 48)

        Returns:
            Filtered list of events
        """
        now = datetime.now(datetime.now().astimezone().tzinfo)
        filtered = []

        for event in events:
            close_time_str = event.get("close_time")
            if not close_time_str:
                continue

            try:
                close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                hours_until_close = (close_time - now).total_seconds() / 3600

                if min_hours <= hours_until_close <= max_hours:
                    filtered.append(event)
            except:
                continue

        return filtered


async def main():
    """Main exploration function."""
    print("=" * 70)
    print("KALSHI API EXPLORATION SCRIPT")
    print("=" * 70)
    print("\nPurpose: Understand Kalshi API structure before building pipeline")
    print("Focus: Find 5 high-quality binary YES/NO markets closing in 24-48h\n")

    # Initialize explorer (no API key needed for public data)
    explorer = KalshiExplorer()

    # Step 1: Fetch open markets (not events!)
    print("\n" + "=" * 70)
    print("STEP 1: Fetching open markets from Kalshi API")
    print("=" * 70)

    all_markets = await explorer.get_markets(limit=1000, status="open")
    print(f"\n✓ Total markets fetched: {len(all_markets)}")

    # Immediately check for simple binary vs multivariate
    multivariate_count = sum(1 for m in all_markets if m.get("mve_selected_legs"))
    simple_count = len(all_markets) - multivariate_count
    print(f"  • Simple markets: {simple_count}")
    print(f"  • Multivariate/parlay markets: {multivariate_count}")

    # Step 2: Show sample market structure FIRST
    print("\n" + "=" * 70)
    print("STEP 2: Examining raw market structure")
    print("=" * 70)

    if all_markets:
        print("\nSample market JSON (first market):")
        print(json.dumps(all_markets[0], indent=2))
        print("\nAvailable fields:")
        print(f"  Keys: {list(all_markets[0].keys())}")

    # Step 2b: Show market categories
    print("\n" + "=" * 70)
    print("STEP 2b: Analyzing market categories")
    print("=" * 70)

    categories = {}
    for market in all_markets:
        cat = market.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat}: {count} markets")

    # Step 3: Analyze close time distribution
    print("\n" + "=" * 70)
    print("STEP 3: Analyzing close time distribution")
    print("=" * 70)

    # Show close time distribution
    now = datetime.now(datetime.now().astimezone().tzinfo)
    time_buckets = {
        "< 24h": 0,
        "24-48h": 0,
        "2-7 days": 0,
        "1-4 weeks": 0,
        "> 1 month": 0,
        "No close time": 0
    }

    for market in all_markets:
        close_time_str = market.get("close_time")
        if not close_time_str:
            time_buckets["No close time"] += 1
            continue

        try:
            close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
            hours_until_close = (close_time - now).total_seconds() / 3600

            if hours_until_close < 0:
                continue  # Already closed
            elif hours_until_close < 24:
                time_buckets["< 24h"] += 1
            elif hours_until_close < 48:
                time_buckets["24-48h"] += 1
            elif hours_until_close < 168:  # 7 days
                time_buckets["2-7 days"] += 1
            elif hours_until_close < 672:  # 4 weeks
                time_buckets["1-4 weeks"] += 1
            else:
                time_buckets["> 1 month"] += 1
        except:
            time_buckets["No close time"] += 1

    print("\nClose time distribution:")
    for bucket, count in time_buckets.items():
        print(f"  • {bucket}: {count} markets")

    # Try different time windows
    print("\n--- Trying different time windows ---")
    windows = [
        (0, 24, "0-24 hours"),
        (24, 48, "24-48 hours"),
        (0, 48, "0-48 hours"),
        (0, 168, "0-7 days"),
        (0, 672, "0-4 weeks"),  # Fallback for exploration
    ]

    best_window = None
    for min_h, max_h, label in windows:
        filtered = explorer.filter_closing_soon(all_markets, min_hours=min_h, max_hours=max_h)
        print(f"  • {label}: {len(filtered)} markets")
        if best_window is None and len(filtered) >= 5:
            best_window = (min_h, max_h, label, filtered)

    # Use best window or default to 0-4 weeks
    if best_window:
        min_h, max_h, label, closing_soon = best_window
        print(f"\n✓ Using {label} window ({len(closing_soon)} markets)")
    else:
        closing_soon = explorer.filter_closing_soon(all_markets, min_hours=0, max_hours=672)
        print(f"\n✓ Using 0-4 weeks window as fallback ({len(closing_soon)} markets)")

    # Show top 10 markets closing soon
    print("\n--- Top 10 Markets Closing Soonest ---")
    for i, market in enumerate(closing_soon[:10], 1):
        explorer.print_market_summary(market, i)

    # Step 4: Filter for binary markets
    if closing_soon:
        print("\n" + "=" * 70)
        print("STEP 4: Filtering for binary YES/NO markets")
        print("=" * 70)

        binary_markets = explorer.filter_binary_markets(closing_soon)
        print(f"\n✓ Found {len(binary_markets)} binary YES/NO markets (out of {len(closing_soon)} total)")

        if binary_markets:
            print("\n--- Sample Binary Markets ---")
            for i, market in enumerate(binary_markets[:5], 1):
                explorer.print_market_summary(market, i)

    # Summary
    print("\n" + "=" * 70)
    print("EXPLORATION SUMMARY")
    print("=" * 70)
    print(f"\n✓ Total open markets: {len(all_markets)}")
    print(f"✓ Markets with viable close times: {len(closing_soon)}")
    if closing_soon:
        binary_count = len(explorer.filter_binary_markets(closing_soon))
        print(f"✓ Binary YES/NO markets: {binary_count}")
    print(f"✓ Categories found: {len(categories)}")
    print("\nKey insights:")
    if closing_soon and len(closing_soon) >= 5:
        print("  ✓ Sufficient markets available for daily selection (need 5)")
    else:
        print("  ⚠️  May need to adjust time window to find 5 markets daily")
    print("\nNext steps for pipeline implementation:")
    print("  1. Implement multi-factor scoring (volume, liquidity, controversy)")
    print("  2. Add LLM-based category classification (Politics→Finance/Sports/etc.)")
    print("  3. Implement hard quota selector (2-1-1-1)")
    print("  4. Add price locking mechanism")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
