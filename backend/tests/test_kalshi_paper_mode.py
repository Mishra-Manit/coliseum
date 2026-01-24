#!/usr/bin/env python3
"""Tests for Kalshi paper-mode behavior."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig


def test_paper_mode_allows_balance_without_auth() -> None:
    client = KalshiClient(KalshiConfig(paper_mode=True))

    async def run() -> None:
        async with client:
            balance = await client.get_balance()
            assert balance.balance > 0

    asyncio.run(run())


def test_paper_mode_places_order_without_auth() -> None:
    client = KalshiClient(KalshiConfig(paper_mode=True))

    async def run() -> None:
        async with client:
            order = await client.place_order(
                ticker="TEST-MARKET",
                side="yes",
                action="buy",
                count=10,
                yes_price=45,
            )
            assert order.order_id.startswith("paper_")
            assert order.status == "executed"
            assert order.remaining_count == 0

    asyncio.run(run())
