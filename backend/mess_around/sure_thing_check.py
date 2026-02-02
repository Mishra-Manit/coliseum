"""Exploration scripts for the Kalshi API."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from coliseum.services.kalshi import KalshiClient, KalshiConfig


async def find_high_volume_markets_closing_soon(
    min_hours: int = 0,
    max_hours: int = 48,
    min_contracts: int = 10_000,
    min_prob: int = 90,
    max_prob: int = 95,
) -> None:
    """Find markets closing within a time range with high volume and probability filter."""
    config = KalshiConfig(paper_mode=True)
    async with KalshiClient(config) as client:
        print(f"Fetching markets closing in {min_hours}-{max_hours} hours...")
        markets = await client.get_markets_closing_in_range(
            min_hours=min_hours,
            max_hours=max_hours,
            limit=10000,
        )

        filtered = []
        for m in markets:
            if m.volume < min_contracts:
                continue

            yes_prob = m.yes_bid if m.yes_bid else m.yes_ask
            no_prob = m.no_bid if m.no_bid else m.no_ask

            yes_in_range = min_prob <= yes_prob <= max_prob
            no_in_range = min_prob <= no_prob <= max_prob

            if yes_in_range or no_in_range:
                filtered.append((m, yes_prob, no_prob))

        print(f"\nFound {len(filtered)} markets with:")
        print(f"  - Closing in {min_hours}-{max_hours} hours")
        print(f"  - Volume >= {min_contracts:,} contracts")
        print(f"  - Probability between {min_prob}-{max_prob}%\n")

        for m, yes_prob, no_prob in sorted(
            filtered, key=lambda x: x[0].volume, reverse=True
        ):
            side = "YES" if min_prob <= yes_prob <= max_prob else "NO"
            prob = yes_prob if side == "YES" else no_prob
            print(f"[{m.ticker}] {m.title}")
            print(f"  {side} @ {prob}¢ | Volume: {m.formatted_volume} | Closes: {m.formatted_close_time}")
            print()


if __name__ == "__main__":
    asyncio.run(find_high_volume_markets_closing_soon())
