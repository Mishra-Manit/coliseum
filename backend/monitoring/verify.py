"""Temp script: re-fetch every row in markets.csv and verify stored results.

Prints any discrepancies and optionally fixes them with --fix.
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

from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig

CSV_PATH = Path(__file__).parent / "markets.csv"

COLUMNS = [
    "ticker", "event_ticker", "title", "subtitle", "side",
    "entry_price", "entry_time", "scheduled_close_time",
    "volume", "open_interest", "result", "close_price", "resolved_at",
]


def _expected_close_price(result: str, side: str) -> str:
    if result in ("yes", "no"):
        return "100" if result == side else "0"
    return ""


async def verify(fix: bool) -> None:
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"Checking {len(rows)} rows...\n")
    discrepancies = 0
    newly_resolved = 0

    async with KalshiClient(config=KalshiConfig()) as client:
        for row in rows:
            ticker = row["ticker"]
            try:
                market = await client.get_market(ticker)
            except Exception as e:
                print(f"  ERROR  {ticker}: {e}")
                continue

            actual_result = market.result or ""
            stored_result = row["result"]
            stored_close = row["close_price"]

            # Case 1: stored as resolved — verify it matches
            if stored_result:
                if actual_result != stored_result:
                    print(f"  MISMATCH  {ticker}  stored={stored_result!r}  actual={actual_result!r}")
                    discrepancies += 1
                    if fix:
                        row["result"] = actual_result
                        row["close_price"] = _expected_close_price(actual_result, row["side"])
                        row["resolved_at"] = datetime.now(timezone.utc).isoformat()

                expected_close = _expected_close_price(stored_result, row["side"])
                if stored_close != expected_close:
                    print(f"  BAD PRICE {ticker}  stored={stored_close!r}  expected={expected_close!r}  result={stored_result!r}  side={row['side']!r}")
                    discrepancies += 1
                    if fix:
                        row["close_price"] = expected_close

            # Case 2: not yet resolved — check if it has resolved now
            elif actual_result:
                print(f"  NOW RESOLVED  {ticker}  result={actual_result!r}  side={row['side']!r}")
                newly_resolved += 1
                if fix:
                    row["result"] = actual_result
                    row["close_price"] = _expected_close_price(actual_result, row["side"])
                    row["resolved_at"] = datetime.now(timezone.utc).isoformat()

    print(f"\nDiscrepancies: {discrepancies}  |  Newly resolved: {newly_resolved}")

    if fix and (discrepancies or newly_resolved):
        with tempfile.NamedTemporaryFile("w", dir=CSV_PATH.parent, delete=False, newline="", suffix=".tmp") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
            tmp_path = tmp.name
        shutil.move(tmp_path, CSV_PATH)
        print("CSV updated.")
    elif not fix and (discrepancies or newly_resolved):
        print("Run with --fix to apply corrections.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify markets.csv against Kalshi")
    parser.add_argument("--fix", action="store_true", help="Apply corrections to the CSV")
    args = parser.parse_args()
    asyncio.run(verify(args.fix))


if __name__ == "__main__":
    main()
