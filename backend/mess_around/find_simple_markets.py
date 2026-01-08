#!/usr/bin/env python3
"""
Find simple binary markets by examining event_tickers from markets.
Strategy: Get markets, find unique event_tickers, fetch those events' markets.
"""

import asyncio
import httpx
import json
from collections import Counter


async def find_simple_markets():
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    print("=" * 70)
    print("STRATEGY: Find event_tickers from markets, then get all their markets")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Get some markets and extract event_tickers
        print("\nStep 1: Fetching 500 markets...")
        response = await client.get(
            f"{BASE_URL}/markets",
            params={"limit": 500, "status": "open"}
        )

        markets = response.json().get("markets", [])
        print(f"✓ Got {len(markets)} markets")

        # Extract unique event_tickers
        event_tickers = list(set(m.get("event_ticker") for m in markets if m.get("event_ticker")))
        print(f"✓ Found {len(event_tickers)} unique event_tickers")

        # Step 2: Try fetching markets for a few event_tickers
        print(f"\nStep 2: Fetching markets for first 10 event_tickers...")

        simple_market_count = 0
        multivariate_market_count = 0

        for i, event_ticker in enumerate(event_tickers[:10], 1):
            print(f"\n{i}. Event: {event_ticker}")

            try:
                response = await client.get(
                    f"{BASE_URL}/events/{event_ticker}/markets"
                )

                if response.status_code == 200:
                    event_markets = response.json().get("markets", [])
                    simple = sum(1 for m in event_markets if not m.get("mve_selected_legs"))
                    multi = len(event_markets) - simple

                    simple_market_count += simple
                    multivariate_market_count += multi

                    print(f"   Markets: {len(event_markets)} total")
                    print(f"   • Simple: {simple}")
                    print(f"   • Multivariate: {multi}")

                    # If we found simple markets, show one
                    if simple > 0:
                        print(f"\n   🎉 FOUND SIMPLE MARKETS!")
                        for m in event_markets:
                            if not m.get("mve_selected_legs"):
                                print(f"\n   Sample simple market:")
                                print(f"   Ticker: {m.get('ticker')}")
                                print(f"   Title: {m.get('title')}")
                                print(f"   Subtitle: {m.get('subtitle')}")
                                print(f"   Volume: ${m.get('volume', 0):,}")
                                print(f"   YES bid/ask: {m.get('yes_bid', 0)/100:.2%} / {m.get('yes_ask', 0)/100:.2%}")
                                print(f"   Close time: {m.get('close_time')}")

                                # Show full JSON of first simple market found
                                print(f"\n   Full JSON structure:")
                                print(json.dumps(m, indent=2)[:1500])
                                return  # Found what we need!

                elif response.status_code == 404:
                    print(f"   ⚠️  404 - Event not found or no markets")
                else:
                    print(f"   ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Simple markets found: {simple_market_count}")
        print(f"Multivariate markets found: {multivariate_market_count}")

        if simple_market_count == 0:
            print("\n⚠️  No simple binary markets found in current open markets!")
            print("This might be because Kalshi is currently focused on sports parlays.")


if __name__ == "__main__":
    asyncio.run(find_simple_markets())
