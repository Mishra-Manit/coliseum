#!/usr/bin/env python3
"""
Test to compare KalshiClient pagination vs direct API calls.
"""

import asyncio
import logging
from coliseum.services.kalshi.client import KalshiClient

# Enable debug logging to see HTTP requests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

async def main():
    print("=" * 70)
    print("Testing KalshiClient with 72-hour window")
    print("=" * 70)

    async with KalshiClient() as client:
        # Fetch markets closing within 72 hours
        markets = await client.get_markets_closing_within_hours(
            hours=72,
            limit=10000,
            status="open"
        )

        print(f"\n📊 Total markets fetched: {len(markets)}")

        # Filter by volume
        high_volume = [m for m in markets if m.volume >= 10000]
        print(f"✅ Markets with volume >= 10,000: {len(high_volume)}")

        # Show some examples
        print(f"\n📋 Sample high-volume markets:")
        for i, m in enumerate(high_volume[:5], 1):
            print(f"  {i}. {m.ticker} - Volume: {m.volume:,} - Close: {m.close_time}")

    print("\n" + "=" * 70)
    print("Testing KalshiClient with 24-hour window")
    print("=" * 70)

    async with KalshiClient() as client:
        # Fetch markets closing within 24 hours
        markets = await client.get_markets_closing_within_hours(
            hours=24,
            limit=10000,
            status="open"
        )

        print(f"\n📊 Total markets fetched: {len(markets)}")

        # Filter by volume
        high_volume = [m for m in markets if m.volume >= 10000]
        print(f"✅ Markets with volume >= 10,000: {len(high_volume)}")

        # Show some examples
        print(f"\n📋 Sample high-volume markets:")
        for i, m in enumerate(high_volume[:5], 1):
            print(f"  {i}. {m.ticker} - Volume: {m.volume:,} - Close: {m.close_time}")

if __name__ == "__main__":
    asyncio.run(main())
