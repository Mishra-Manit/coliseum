#!/usr/bin/env python3
"""
Find events with active markets in specific categories.
"""

import asyncio
import httpx
import json


async def find_active_events():
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch events with different filters
        print("=" * 70)
        print("Searching for events with active markets...")
        print("=" * 70)

        # Try fetching by specific series
        test_series = [
            "KXNFLGAME",  # NFL games
            "KXNBAGAME",  # NBA games
            "TRUMPJOB",   # Trump job approval
            "FED",        # Federal Reserve
            "INXD",       # Stock market
        ]

        for series in test_series:
            print(f"\n📊 Trying series: {series}")

            try:
                # Get markets for this series
                response = await client.get(
                    f"{BASE_URL}/markets",
                    params={"series_ticker": series, "limit": 10, "status": "open"}
                )

                if response.status_code == 200:
                    markets = response.json().get("markets", [])
                    print(f"   ✓ Found {len(markets)} markets")

                    if markets:
                        # Check if any are simple
                        simple = [m for m in markets if not m.get("mve_selected_legs")]

                        if simple:
                            print(f"   🎉 Found {len(simple)} SIMPLE binary markets!")
                            m = simple[0]
                            print(f"\n   Sample market:")
                            print(f"   Title: {m.get('title')}")
                            print(f"   Subtitle: {m.get('subtitle')}")
                            print(f"   Ticker: {m.get('ticker')}")
                            print(f"   Close: {m.get('close_time')}")
                            print(f"   YES: {m.get('yes_bid', 0)/100:.2%} bid / {m.get('yes_ask', 0)/100:.2%} ask")
                            print(f"   Volume: ${m.get('volume', 0):,}")
                            print(f"\n   Full structure:")
                            print(json.dumps(m, indent=2)[:2000])
                            return True
                        else:
                            print(f"   ⚠️  All {len(markets)} markets are multivariate")
                else:
                    print(f"   ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 70)
    print("❌ Could not find simple binary markets")
    print("=" * 70)
    print("\nPossible reasons:")
    print("1. Kalshi is currently focused on sports parlays/multivariate markets")
    print("2. Simple markets may require authentication to access")
    print("3. Need to check different series/categories")
    return False


if __name__ == "__main__":
    asyncio.run(find_active_events())
