"""Market monitoring script for Kalshi near-decided markets.

Builds a CSV dataset to identify which event types consistently resolve
to 100 once they reach the 92-96% probability range.

Commands:
  collect  - fetch all pre-filtered markets and add new entries to CSV
  update   - check unresolved markets in CSV and record close prices
"""

import argparse
import asyncio
import csv
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from coliseum.config import get_settings
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig

CSV_PATH = Path(__file__).parent / "markets.csv"

COLUMNS = [
    "ticker",
    "event_ticker",
    "title",
    "subtitle",
    "side",
    "entry_price",
    "entry_time",
    "scheduled_close_time",
    "volume",
    "open_interest",
    "result",
    "close_price",
    "resolved_at",
]


def _load_existing_keys() -> set[tuple[str, str]]:
    """Return (ticker, side) pairs already recorded in the CSV."""
    if not CSV_PATH.exists():
        return set()
    with open(CSV_PATH, newline="") as f:
        return {(row["ticker"], row["side"]) for row in csv.DictReader(f)}


def _append_rows(rows: list[dict]) -> None:
    write_header = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _make_row(m, side: str, entry_price: int, now: str) -> dict:
    return {
        "ticker": m.ticker,
        "event_ticker": m.event_ticker,
        "title": m.title,
        "subtitle": m.subtitle,
        "side": side,
        "entry_price": entry_price,
        "entry_time": now,
        "scheduled_close_time": m.close_time.isoformat() if m.close_time else "",
        "volume": m.volume,
        "open_interest": m.open_interest,
        "result": "",
        "close_price": "",
        "resolved_at": "",
    }


async def collect() -> None:
    """Fetch all pre-filtered markets and append new ones to the CSV."""
    settings = get_settings()
    s = settings.scout
    now = datetime.now(timezone.utc).isoformat()

    async with KalshiClient(config=KalshiConfig()) as client:
        markets = await client.get_markets_closing_in_range(
            min_hours=s.min_close_hours,
            max_hours=s.max_close_hours,
            limit=s.market_fetch_limit,
            status="open",
        )

    # Same pre-filters as scout/main.py
    markets = [m for m in markets if m.volume >= s.min_volume]

    existing = _load_existing_keys()
    new_rows: list[dict] = []

    for m in markets:
        yes_in_range = s.min_price <= (m.yes_ask or 0) <= s.max_price
        no_in_range = s.min_price <= (m.no_ask or 0) <= s.max_price

        if (
            yes_in_range
            and m.yes_ask is not None
            and m.yes_bid is not None
            and (m.yes_ask - m.yes_bid) <= s.max_spread_cents
            and (m.ticker, "yes") not in existing
        ):
            new_rows.append(_make_row(m, "yes", m.yes_ask, now))
            existing.add((m.ticker, "yes"))

        if (
            no_in_range
            and m.no_ask is not None
            and m.no_bid is not None
            and (m.no_ask - m.no_bid) <= s.max_spread_cents
            and (m.ticker, "no") not in existing
        ):
            new_rows.append(_make_row(m, "no", m.no_ask, now))
            existing.add((m.ticker, "no"))

    _append_rows(new_rows)
    print(f"Collected {len(new_rows)} new entries. Total in CSV: {len(existing)}.")


async def update() -> None:
    """Check unresolved markets in the CSV and record close prices."""
    if not CSV_PATH.exists():
        print("No CSV found. Run collect first.")
        return

    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    unresolved = [r for r in rows if not r["close_price"] and not r["result"]]
    if not unresolved:
        print(f"All {len(rows)} markets already resolved.")
        return

    print(f"Checking {len(unresolved)} unresolved markets...")
    updated = 0

    async with KalshiClient(config=KalshiConfig()) as client:
        for row in unresolved:
            try:
                market = await client.get_market(row["ticker"])
                if market.result in ("yes", "no"):
                    row["result"] = market.result
                    row["close_price"] = 100 if market.result == row["side"] else 0
                    row["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    updated += 1
                elif market.result:
                    # voided, scalar, or other non-binary outcome — exclude from analysis
                    row["result"] = market.result
                    row["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    updated += 1
            except Exception as e:
                print(f"  Error fetching {row['ticker']}: {e}")

    with tempfile.NamedTemporaryFile("w", dir=CSV_PATH.parent, delete=False, newline="", suffix=".tmp") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        tmp_path = tmp.name
    shutil.move(tmp_path, CSV_PATH)

    total_resolved = sum(1 for r in rows if r["close_price"])
    print(f"Updated {updated} markets. Total resolved: {total_resolved}/{len(rows)}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kalshi market monitoring")
    parser.add_argument("command", choices=["collect", "update"])
    args = parser.parse_args()

    if args.command == "collect":
        asyncio.run(collect())
    else:
        asyncio.run(update())


if __name__ == "__main__":
    main()
