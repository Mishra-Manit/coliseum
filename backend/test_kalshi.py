#!/usr/bin/env python3
"""
Test script for KalshiService.
Run with: python test_kalshi.py
"""

import asyncio
from datetime import datetime

from services.kalshi_service import KalshiService


def format_market(m: dict, index: int) -> str:
    """Format a market for display."""
    ticker = m.get("ticker", "N/A")
    title = m.get("title", "No title")
    subtitle = m.get("subtitle", "")
    yes_bid = m.get("yes_bid", 0)
    yes_ask = m.get("yes_ask", 0)
    volume = m.get("volume", 0)
    close_time = m.get("close_time", "N/A")

    # Parse close time for display
    if close_time != "N/A":
        try:
            ct = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
            close_display = ct.strftime("%Y-%m-%d %H:%M UTC")
        except:
            close_display = close_time
    else:
        close_display = "N/A"

    return f"""
{index}. {title}
   Subtitle: {subtitle}
   Ticker: {ticker}
   YES Price: {yes_bid}¢ bid / {yes_ask}¢ ask
   Volume: ${volume:,}
   Closes: {close_display}
"""


async def main():
    print("=" * 60)
    print("KALSHI SERVICE TEST (using actual KalshiService)")
    print("=" * 60)

    service = KalshiService()

    try:
        # Test 1: Get events closing today using the updated service
        print("\n⏰ Testing get_events_closing_today()...")
        closing_today = await service.get_events_closing_today()
        print(f"Found {len(closing_today)} events closing within 24 hours")

        if closing_today:
            print("\n--- EVENTS CLOSING TODAY ---")
            for i, m in enumerate(closing_today[:10], 1):
                print(format_market(m, i))
            if len(closing_today) > 10:
                print(f"   ... and {len(closing_today) - 10} more")
        else:
            print("No events closing in the next 24 hours.")

        # Test 2: Get market details for first market
        if closing_today:
            print("\n" + "=" * 60)
            test_ticker = closing_today[0].get("ticker")
            print(f"🔍 Testing get_market_details('{test_ticker}')...")
            details = await service.get_market_details(test_ticker)
            if details:
                print(f"\nMarket Details:")
                print(f"  Title: {details.get('title')}")
                print(f"  Status: {details.get('status')}")
                print(f"  Result: {details.get('result') or 'Not settled'}")
                print(f"  Category: {details.get('category')}")
                print(f"  Volume: ${details.get('volume', 0):,}")
                print(f"  Open Interest: ${details.get('open_interest', 0):,}")

        # Test 3: Get current price
        if closing_today:
            print("\n" + "=" * 60)
            test_ticker = closing_today[0].get("ticker")
            print(f"💰 Testing get_market_price('{test_ticker}')...")
            price = await service.get_market_price(test_ticker)
            if price:
                print(f"  YES Price: {price:.2%}")

        # Test 4: Check series-based fetching
        print("\n" + "=" * 60)
        print("📊 Testing get_markets_by_series('KXHIGHNY')...")
        nyc_markets = await service.get_markets_by_series("KXHIGHNY")
        print(f"Found {len(nyc_markets)} NYC temperature markets")
        if nyc_markets:
            print(f"  Example: {nyc_markets[0].get('title')}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.close()

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
