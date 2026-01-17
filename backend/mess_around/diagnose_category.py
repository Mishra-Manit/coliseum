#!/usr/bin/env python3
"""
Diagnostic script to inspect what fields the Kalshi API actually returns for markets.
This will help us understand why category is showing as "N/A".
"""

import asyncio
import json
import logging
from coliseum.services.kalshi.client import KalshiClient

# Enable debug logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("=" * 70)
    print("Diagnosing Kalshi API Market Response")
    print("=" * 70)

    async with KalshiClient() as client:
        # Fetch a few markets
        markets = await client.get_markets(limit=3, status="open")

        print(f"\n📊 Fetched {len(markets)} markets")

        if markets:
            print("\n" + "=" * 70)
            print("First market object (Python parsed):")
            print("=" * 70)
            market = markets[0]
            print(f"Ticker: {market.ticker}")
            print(f"Title: {market.title}")
            print(f"Category: {market.category}")  # This is the issue field
            print(f"Event Ticker: {market.event_ticker}")

            # Now let's see the RAW API response
            print("\n" + "=" * 70)
            print("Making raw API call to see actual response fields:")
            print("=" * 70)

            # Make a raw request to see what the API actually returns
            raw_response = await client._request("GET", "markets", params={"limit": 1, "status": "open"})

            if "markets" in raw_response and raw_response["markets"]:
                raw_market = raw_response["markets"][0]
                print("\nRaw market data (first market):")
                print(json.dumps(raw_market, indent=2))

                print("\n" + "=" * 70)
                print("Field Analysis:")
                print("=" * 70)
                print(f"Has 'category' field: {'category' in raw_market}")
                if 'category' in raw_market:
                    print(f"Category value: {raw_market['category']}")

                # Check for related fields that might contain category info
                potential_category_fields = [
                    'category', 'series_ticker', 'event_ticker', 'tags',
                    'markets_categories', 'market_type', 'series'
                ]

                print("\nChecking for potential category-related fields:")
                for field in potential_category_fields:
                    if field in raw_market:
                        print(f"  ✓ {field}: {raw_market[field]}")
                    else:
                        print(f"  ✗ {field}: NOT PRESENT")

if __name__ == "__main__":
    asyncio.run(main())
