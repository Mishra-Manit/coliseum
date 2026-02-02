"""Fetch and print Kalshi account details from .env credentials."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

from coliseum.services.kalshi import KalshiClient, KalshiConfig


def _load_env(backend_root: Path) -> None:
    env_path = backend_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _load_private_key(backend_root: Path, key_path: str) -> str:
    path = Path(key_path)
    if not path.is_absolute():
        path = backend_root / path
    if not path.exists():
        raise FileNotFoundError(f"Private key not found: {path}")
    return path.read_text(encoding="utf-8")


def _to_serializable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    return value


def _print_section(title: str, items: list[Any]) -> None:
    print(f"\n== {title} ({len(items)}) ==")
    for item in items:
        print(json.dumps(_to_serializable(item), default=str))


def _normalize_string_fields(records: list[dict[str, Any]], fields: list[str]) -> None:
    for record in records:
        for field in fields:
            if record.get(field) is None:
                record[field] = ""


async def _run(orders_limit: int, fills_limit: int) -> None:
    backend_root = Path(__file__).resolve().parent.parent
    _load_env(backend_root)

    api_key = _require_env("KALSHI_API_KEY")
    key_path = _require_env("RSA_PRIVATE_KEY_PATH")
    private_key_pem = _load_private_key(backend_root, key_path)

    config = KalshiConfig(paper_mode=False)
    async with KalshiClient(config, api_key, private_key_pem) as client:
        balance = await client.get_balance()
        print("== BALANCE ==")
        print(
            json.dumps(
                {
                    "balance_cents": balance.balance,
                    "payout_cents": balance.payout,
                    "balance_usd": balance.balance_usd,
                    "payout_usd": balance.payout_usd,
                }
            )
        )

        positions = await client.get_positions()
        _print_section("POSITIONS", positions)

        try:
            orders = await client.get_orders(limit=orders_limit)
            _print_section("ORDERS", orders)
        except ValidationError:
            raw_orders = await client._paginate(
                "portfolio/orders",
                {"limit": min(orders_limit, 200)},
                orders_limit,
                "orders",
                auth_required=True,
            )
            _normalize_string_fields(
                raw_orders,
                ["order_group_id", "client_order_id", "event_ticker", "ticker"],
            )
            _print_section("ORDERS", raw_orders)

        fills = await client.get_fills(limit=fills_limit)
        _print_section("FILLS", fills)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print Kalshi account details using .env credentials."
    )
    parser.add_argument(
        "--orders-limit",
        type=int,
        default=200,
        help="Max number of orders to fetch",
    )
    parser.add_argument(
        "--fills-limit",
        type=int,
        default=200,
        help="Max number of fills to fetch",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.orders_limit, args.fills_limit))


if __name__ == "__main__":
    main()
