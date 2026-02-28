"""Portfolio sync helpers for Kalshi account reconciliation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from coliseum.services.kalshi import KalshiClient
from coliseum.services.kalshi.models import Position as KalshiPosition
from coliseum.storage.state import (
    ClosedPosition,
    PortfolioState,
    PortfolioStats,
    Position,
    load_state,
    save_state,
)

logger = logging.getLogger(__name__)


def normalize_kalshi_side(side: str | None) -> str | None:
    """Normalize side text to YES/NO for state reconciliation."""
    return _normalize_side(side)


def normalize_probability_price(value: Any) -> float | None:
    """Normalize Kalshi price to decimal probability (0-1)."""
    return _normalize_price(value)


def extract_fill_count(fill: dict[str, Any]) -> int | None:
    """Extract filled contract count from a fill payload."""
    return _extract_fill_count(fill)


def extract_fill_price(fill: dict[str, Any], side: str | None) -> float | None:
    """Extract fill price from a fill payload in decimal probability format."""
    return _extract_fill_price(fill, side)


async def fetch_market_side_price(
    client: KalshiClient,
    market_ticker: str,
    side: str,
) -> float | None:
    """Fetch best available bid/ask price for a side in decimal probability format."""
    market = await client.get_market(market_ticker)
    if side == "YES":
        price = normalize_probability_price(market.yes_bid) or 0.0
        if price == 0.0:
            price = normalize_probability_price(market.yes_ask) or 0.0
    else:
        price = normalize_probability_price(market.no_bid) or 0.0
        if price == 0.0:
            price = normalize_probability_price(market.no_ask) or 0.0
    return price or None


def _normalize_side(side: str | None) -> str | None:
    if not side:
        return None
    normalized = side.strip().upper()
    if normalized in {"YES", "NO"}:
        return normalized
    return None


def _normalize_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    if price > 1:
        return price / 100
    return price


def _extract_fill_count(fill: dict[str, Any]) -> int | None:
    for key in ("count", "contracts", "quantity", "filled_count", "size"):
        if key in fill and fill[key] is not None:
            try:
                count = int(fill[key])
            except (TypeError, ValueError):
                continue
            if count > 0:
                return count
    return None


def _extract_fill_price(fill: dict[str, Any], side: str | None) -> float | None:
    if side == "NO":
        no_price = _normalize_price(fill.get("no_price"))
        if no_price is not None:
            return no_price
        yes_price = _normalize_price(
            fill.get("yes_price") or fill.get("price") or fill.get("fill_price")
        )
        if yes_price is not None:
            return 1.0 - yes_price
        return None

    direct = _normalize_price(
        fill.get("yes_price") or fill.get("price") or fill.get("fill_price") or fill.get("avg_price")
    )
    return direct


def _compute_average_entries(
    fills: list[dict[str, Any]],
) -> dict[tuple[str, str], float]:
    """Compute weighted average entry price per ticker and side."""
    totals: dict[tuple[str, str], tuple[float, int]] = {}
    for fill in fills:
        ticker = fill.get("ticker") or fill.get("market_ticker")
        if not ticker:
            continue
        side = _normalize_side(fill.get("side"))
        if not side:
            continue
        action = fill.get("action")
        if action and str(action).lower() not in {"buy", "b"}:
            continue
        count = _extract_fill_count(fill)
        if not count:
            continue
        price = _extract_fill_price(fill, side)
        if price is None:
            continue
        key = (ticker, side)
        total_cost, total_count = totals.get(key, (0.0, 0))
        totals[key] = (total_cost + price * count, total_count + count)
    return {
        key: total_cost / total_count
        for key, (total_cost, total_count) in totals.items()
        if total_count > 0
    }


def _map_kalshi_position(
    kalshi_pos: KalshiPosition,
    avg_entry: float,
    current_price: float,
    existing: Position | None,
) -> Position:
    """Map a Kalshi API position to a local Position model, preserving metadata from existing position."""
    side = _normalize_side(kalshi_pos.side)
    position_id = existing.id if existing else f"pos_{uuid4().hex[:8]}"
    opportunity_id = existing.opportunity_id if existing else f"sync_{uuid4().hex[:8]}"
    contracts = kalshi_pos.contracts
    return Position(
        id=position_id,
        market_ticker=kalshi_pos.market_ticker,
        side=side or "YES",
        contracts=contracts,
        average_entry=avg_entry,
        current_price=current_price,
        opportunity_id=opportunity_id,
    )


async def sync_portfolio_from_kalshi(client: KalshiClient) -> PortfolioState:
    """Fetch live account data from Kalshi and reconcile with state.yaml."""
    if client.config.paper_mode and client.auth is None:
        logger.warning("Skipping sync: Kalshi client in paper mode without auth.")
        return load_state()

    balance = await client.get_balance()
    kalshi_positions = [
        pos for pos in await client.get_positions() if pos.position != 0
    ]
    fills = await client.get_fills()
    avg_entries = _compute_average_entries(fills)

    existing_state = load_state()
    existing_by_key = {
        (pos.market_ticker, pos.side): pos for pos in existing_state.open_positions
    }

    open_positions: list[Position] = []
    for kalshi_pos in kalshi_positions:
        side = _normalize_side(kalshi_pos.side)
        if not side:
            continue
        key = (kalshi_pos.market_ticker, side)
        existing = existing_by_key.get(key)

        current_price = 0.0
        try:
            market = await client.get_market(kalshi_pos.market_ticker)
            if side == "YES":
                current_price = normalize_probability_price(market.yes_bid) or 0.0
                if current_price == 0.0:
                    current_price = normalize_probability_price(market.yes_ask) or 0.0
            else:
                current_price = normalize_probability_price(market.no_bid) or 0.0
                if current_price == 0.0:
                    current_price = normalize_probability_price(market.no_ask) or 0.0
        except Exception as exc:
            logger.warning(
                "Failed to fetch market data for %s: %s",
                kalshi_pos.market_ticker,
                exc,
            )

        if current_price == 0.0 and existing:
            current_price = existing.current_price

        avg_entry = avg_entries.get(key) or 0.0
        if avg_entry == 0.0:
            if current_price > 0:
                avg_entry = current_price
            elif existing:
                avg_entry = existing.average_entry

        open_positions.append(
            _map_kalshi_position(
                kalshi_pos=kalshi_pos,
                avg_entry=avg_entry,
                current_price=current_price,
                existing=existing,
            )
        )

    positions_value = sum(
        position.contracts * position.current_price for position in open_positions
    )
    cash_balance = balance.balance_usd
    total_value = cash_balance + positions_value

    new_state = PortfolioState(
        last_updated=None,
        portfolio=PortfolioStats(
            total_value=total_value,
            cash_balance=cash_balance,
            positions_value=positions_value,
        ),
        open_positions=open_positions,
        closed_positions=existing_state.closed_positions,
        seen_tickers=existing_state.seen_tickers,
    )
    save_state(new_state)
    logger.info(
        "Synced portfolio: cash=$%.2f positions=%d",
        cash_balance,
        len(open_positions),
    )
    return new_state
