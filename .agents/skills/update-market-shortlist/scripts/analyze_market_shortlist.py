#!/usr/bin/env python3
"""Analyze market shortlist candidates from tracked CSV history.

Produces a JSON report with trade counts AND event diversity metrics,
which are critical for conservative shortlist selection.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
CSV_PATH = PROJECT_ROOT / "backend" / "monitoring" / "markets.csv"


def _load_rows() -> tuple[int, list[dict]]:
    """Return (total_tracked, completed_rows)."""
    with CSV_PATH.open(newline="") as handle:
        all_rows = list(csv.DictReader(handle))

    completed: list[dict] = []
    for row in all_rows:
        if row.get("close_price") not in {"0", "100"}:
            continue
        completed.append(
            {
                **row,
                "entry_price": int(row["entry_price"]),
                "won": row["close_price"] == "100",
                "prefix": row["event_ticker"].partition("-")[0],
            }
        )
    return len(all_rows), completed


def _record(rows: list[dict]) -> dict[str, float | int]:
    wins = sum(int(row["won"]) for row in rows)
    losses = len(rows) - wins
    events = len({row["event_ticker"] for row in rows})
    return {
        "n": len(rows),
        "wins": wins,
        "losses": losses,
        "events": events,
        "win_rate": round(wins / len(rows), 4) if rows else 0.0,
    }


def main() -> None:
    total_tracked, rows = _load_rows()
    by_category: dict[str, list[dict]] = defaultdict(list)
    by_prefix: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
        by_prefix[row["prefix"]].append(row)

    gated_prefixes: list[dict[str, object]] = []
    for prefix, prefix_rows in sorted(by_prefix.items()):
        for gate in range(90, 100):
            gated_rows = [row for row in prefix_rows if row["entry_price"] >= gate]
            if len(gated_rows) < 3:
                continue
            record = _record(gated_rows)
            if record["losses"] == 0:
                gated_prefixes.append(
                    {
                        "prefix": prefix,
                        "gate": gate,
                        **record,
                    }
                )

    output = {
        "csv_path": str(CSV_PATH),
        "total_tracked": total_tracked,
        "summary": _record(rows),
        "categories": {
            key: _record(value)
            for key, value in sorted(by_category.items())
        },
        "prefixes": {
            key: _record(value)
            for key, value in sorted(by_prefix.items())
        },
        "zero_loss_prefix_price_gates": sorted(
            gated_prefixes,
            key=lambda item: (-int(item["n"]), str(item["prefix"]), int(item["gate"])),
        ),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
