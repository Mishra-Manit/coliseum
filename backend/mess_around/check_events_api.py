#!/usr/bin/env python3
"""
Check if Kalshi events API contains category information.
"""

import asyncio
import json
import logging
from coliseum.services.kalshi.client import KalshiClient

logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 70)
    print("Checking Kalshi Events API for Category Information")
    print("=" * 70)

    async with KalshiClient() as client:
        # Fetch events with nested markets
        raw_response = await client._request(
            "GET",
            "events",
            params={"limit": 2, "status": "open", "with_nested_markets": "true"}
        )

        if "events" in raw_response and raw_response["events"]:
            event = raw_response["events"][0]
            print("\nFirst event structure:")
            print(json.dumps(event, indent=2))

            print("\n" + "=" * 70)
            print("Checking for category-related fields in events:")
            print("=" * 70)

            potential_fields = [
                'category', 'categories', 'series_ticker', 'tags',
                'markets', 'market_category', 'event_type'
            ]

            for field in potential_fields:
                if field in event:
                    value = event[field]
                    # Truncate if it's a list/dict
                    if isinstance(value, (list, dict)):
                        print(f"  ✓ {field}: {type(value).__name__} (length: {len(value)})")
                    else:
                        print(f"  ✓ {field}: {value}")
                else:
                    print(f"  ✗ {field}: NOT PRESENT")

        # Also check if there's a series or categories endpoint
        print("\n" + "=" * 70)
        print("Checking for series endpoint:")
        print("=" * 70)
        try:
            series_response = await client._request("GET", "series", params={"limit": 1})
            print(f"✓ Series endpoint exists")
            if "series" in series_response and series_response["series"]:
                print("\nFirst series structure:")
                print(json.dumps(series_response["series"][0], indent=2))
        except Exception as e:
            print(f"✗ Series endpoint failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
