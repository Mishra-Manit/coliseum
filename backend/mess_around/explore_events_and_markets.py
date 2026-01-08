#!/usr/bin/env python3
"""
Explore Kalshi events and their child markets.
Purpose: Find simple binary markets by looking at events first.
"""

import asyncio
import httpx
from datetime import datetime
import json


async def explore_events_approach():
    """Try fetching events and then their markets."""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    # Step 1: Fetch some events
    print("=" * 70)
    print("Fetching events...")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/events",
            params={"limit": 50, "status": "open"}
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        data = response.json()
        events = data.get("events", [])
        print(f"\n✓ Found {len(events)} events\n")

        # Show a few event examples
        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event.get('title')}")
            print(f"   Ticker: {event.get('event_ticker')}")
            print(f"   Category: {event.get('category')}")
            print()

        # Step 2: Pick an event and get its markets
        if events:
            print("=" * 70)
            print(f"Fetching markets for event: {events[0].get('title')}")
            print("=" * 70)

            event_ticker = events[0].get("event_ticker")
            print(f"\nRequesting: {BASE_URL}/events/{event_ticker}/markets")

            try:
                response = await client.get(
                    f"{BASE_URL}/events/{event_ticker}/markets"
                )
                print(f"Response status: {response.status_code}")
            except Exception as e:
                print(f"Error fetching markets: {e}")
                return

            if response.status_code == 200:
                markets_data = response.json()
                markets = markets_data.get("markets", [])

                print(f"\n✓ Found {len(markets)} market(s) for this event\n")

                # Analyze these markets
                multivariate = sum(1 for m in markets if m.get("mve_selected_legs"))
                simple = len(markets) - multivariate

                print(f"  • Simple binary markets: {simple}")
                print(f"  • Multivariate markets: {multivariate}\n")

                if simple > 0:
                    print("🎉 Found simple binary markets!")
                    print("\nSample simple market:")
                    for m in markets:
                        if not m.get("mve_selected_legs"):
                            print(json.dumps(m, indent=2)[:500])
                            break
                else:
                    print("All markets for this event are multivariate.")
                    if markets:
                        print("\nSample market:")
                        print(json.dumps(markets[0], indent=2)[:1000])
            else:
                print(f"\n❌ Error fetching markets: {response.status_code}")
                print(f"Response: {response.text[:500]}")


if __name__ == "__main__":
    asyncio.run(explore_events_approach())
