"""One-shot backfill script: adds event_title and category columns to markets.csv."""

import asyncio
import csv
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig

CSV_PATH = Path(__file__).parent / "markets.csv"

COLUMNS = [
    "ticker", "event_ticker", "title", "subtitle", "side",
    "entry_price", "entry_time", "scheduled_close_time",
    "volume", "open_interest", "result", "close_price", "resolved_at",
    "event_title", "category",
]


async def fetch_event_meta(
    client: KalshiClient, event_ticker: str
) -> dict[str, str]:
    """Return event_title and category for a ticker, or empty strings on error."""
    try:
        event = await client.get_event(event_ticker)
        return {"event_title": event.get("title", ""), "category": event.get("category", "")}
    except Exception as e:
        print(f"  Warning: could not fetch {event_ticker}: {e}")
        return {"event_title": "", "category": ""}


async def backfill() -> None:
    """Backfill event_title and category columns into markets.csv."""
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    unique_tickers = list(dict.fromkeys(r["event_ticker"] for r in rows))
    total = len(unique_tickers)
    lookup: dict[str, dict[str, str]] = {}

    async with KalshiClient(config=KalshiConfig()) as client:
        for i, ticker in enumerate(unique_tickers, start=1):
            print(f"Fetching event {i}/{total}: {ticker}...")
            lookup[ticker] = await fetch_event_meta(client, ticker)
            await asyncio.sleep(0.1)

    updated_rows = [
        {**row, **lookup.get(row["event_ticker"], {"event_title": "", "category": ""})}
        for row in rows
    ]

    with tempfile.NamedTemporaryFile("w", dir=CSV_PATH.parent, delete=False, newline="", suffix=".tmp") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(updated_rows)
        tmp_path = tmp.name
    shutil.move(tmp_path, CSV_PATH)

    print(f"Backfilled {total} unique events across {len(rows)} rows.")


if __name__ == "__main__":
    asyncio.run(backfill())
