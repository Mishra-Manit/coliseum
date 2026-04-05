"""Portfolio sync helpers for Kalshi account reconciliation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

from coliseum.services.kalshi import KalshiClient
from coliseum.services.kalshi.models import Market, Position as KalshiPosition
from coliseum.services.supabase.repositories.opportunities import load_opportunity_by_ticker_from_db
from coliseum.services.supabase.repositories.portfolio import load_state_from_db
from coliseum.storage.state import (
    ClosedPosition,
    PortfolioState,
    PortfolioStats,
    Position,
)

logger = logging.getLogger(__name__)


async def fetch_market_side_price(
    client: KalshiClient,
    market_ticker: str,
    side: str,
) -> float | None:
    """Fetch best available bid/ask price for a side in decimal probability format."""
    market = await client.get_market(market_ticker)

    # For finalized markets, use the resolution result directly.
    # Bid/ask values are meaningless artifacts after settlement.
    if market.status == "finalized" and market.result:
        result = market.result.lower()
        if side == "YES":
            if result == "yes":
                return 1.0
            else:
                return 0.0
        else:
            if result == "no":
                return 1.0
            else:
                return 0.0

    if market.status == "closed":
        return None

    return resolve_market_price(market, side)


def normalize_kalshi_side(side: str | None) -> str | None:
    """Normalize side text to YES/NO for state reconciliation."""
    if not side:
        return None
    normalized = side.strip().upper()
    if normalized in {"YES", "NO"}:
        return normalized
    return None


def normalize_probability_price(value: Any) -> float | None:
    """Normalize Kalshi price to decimal probability (0-1)."""
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


def resolve_market_price(market: "Market", side: str) -> float | None:
    """Resolve best available price for a side, with cross-side fallback.

    Priority: direct bid → direct ask → derived from opposite ask → derived from opposite bid.
    Returns None for closed/pending-settlement markets or when all sources are zero.
    """
    if market.status == "closed":
        return None
    if side == "YES":
        price = normalize_probability_price(market.yes_bid) or 0.0
        if price == 0.0:
            price = normalize_probability_price(market.yes_ask) or 0.0
        if price == 0.0 and market.no_ask > 0:
            price = normalize_probability_price(100 - market.no_ask) or 0.0
        if price == 0.0 and market.no_bid > 0:
            price = normalize_probability_price(100 - market.no_bid) or 0.0
    else:
        price = normalize_probability_price(market.no_bid) or 0.0
        if price == 0.0:
            price = normalize_probability_price(market.no_ask) or 0.0
        if price == 0.0 and market.yes_ask > 0:
            price = normalize_probability_price(100 - market.yes_ask) or 0.0
        if price == 0.0 and market.yes_bid > 0:
            price = normalize_probability_price(100 - market.yes_bid) or 0.0
    return price or None


def extract_fill_count(fill: dict[str, Any]) -> int | None:
    """Extract filled contract count from a fill payload."""
    for key in ("count_fp", "count", "contracts", "quantity", "filled_count", "size"):
        if key in fill and fill[key] is not None:
            try:
                count = int(float(fill[key]))
            except (TypeError, ValueError):
                continue
            if count > 0:
                return count
    return None


def extract_fill_price(fill: dict[str, Any], side: str | None) -> float | None:
    """Extract fill price from a fill payload in decimal probability format."""
    if side == "NO":
        no_price = normalize_probability_price(
            fill.get("no_price_dollars") or fill.get("no_price")
        )
        if no_price is not None:
            return no_price
        yes_price = normalize_probability_price(
            fill.get("yes_price_dollars") or fill.get("yes_price")
            or fill.get("price") or fill.get("fill_price")
        )
        if yes_price is not None:
            return 1.0 - yes_price
        return None

    return normalize_probability_price(
        fill.get("yes_price_dollars") or fill.get("yes_price")
        or fill.get("price") or fill.get("fill_price") or fill.get("avg_price")
    )


def _compute_average_entries(
    fills: list[dict[str, Any]],
) -> dict[tuple[str, str], float]:
    """Compute weighted average entry price per ticker and side."""
    totals: dict[tuple[str, str], tuple[float, int]] = {}
    for fill in fills:
        ticker = fill.get("ticker") or fill.get("market_ticker")
        if not ticker:
            continue
        side = normalize_kalshi_side(fill.get("side"))
        if not side:
            continue
        action = fill.get("action")
        if action and str(action).lower() not in {"buy", "b"}:
            continue
        count = extract_fill_count(fill)
        if not count:
            continue
        price = extract_fill_price(fill, side)
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
    resolved_opportunity_id: str | None = None,
) -> Position:
    """Map a Kalshi API position to a local Position model, preserving metadata from existing position."""
    side = normalize_kalshi_side(kalshi_pos.side)
    if existing:
        position_id = existing.id
    else:
        position_id = f"pos_{uuid4().hex[:8]}"
    opportunity_id = resolved_opportunity_id
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
    balance = await client.get_balance()
    kalshi_positions = [
        pos for pos in await client.get_positions() if pos.position != 0
    ]
    fills = await client.get_fills()
    avg_entries = _compute_average_entries(fills)

    existing_state = await load_state_from_db()
    existing_by_key = {
        (pos.market_ticker, pos.side): pos for pos in existing_state.open_positions
    }

    # Fetch all market prices concurrently (avoids N+1 sequential API calls)
    market_results = await asyncio.gather(
        *[client.get_market(pos.market_ticker) for pos in kalshi_positions],
        return_exceptions=True,
    )
    markets: dict[str, Any] = {}
    for pos, result in zip(kalshi_positions, market_results):
        if isinstance(result, Exception):
            logger.warning(
                "Failed to fetch market data for %s: %s",
                pos.market_ticker,
                result,
            )
        else:
            markets[pos.market_ticker] = result

    open_positions: list[Position] = []
    for kalshi_pos in kalshi_positions:
        side = normalize_kalshi_side(kalshi_pos.side)
        if not side:
            continue
        key = (kalshi_pos.market_ticker, side)
        existing = existing_by_key.get(key)

        current_price = 0.0
        market = markets.get(kalshi_pos.market_ticker)
        if market:
            current_price = resolve_market_price(market, side) or 0.0
        if current_price == 0.0 and existing:
            current_price = existing.current_price

        avg_entry = avg_entries.get(key) or 0.0
        if avg_entry == 0.0:
            if current_price > 0:
                avg_entry = current_price
            elif existing:
                avg_entry = existing.average_entry

        # Resolve opportunity_id: prefer a real opp_ ID from existing record, then look
        # up the opportunity file by market ticker, else None. Deliberately skip any
        # legacy sync_ IDs (generated by old code when no existing record was found) so
        # they don't get perpetuated across reconciliation runs.
        if existing:
            existing_opp_id = existing.opportunity_id
        else:
            existing_opp_id = None
        if existing_opp_id and existing_opp_id.startswith("opp_"):
            opp_id = existing_opp_id
        else:
            opp = await load_opportunity_by_ticker_from_db(kalshi_pos.market_ticker)
            if opp:
                opp_id = opp.id
            else:
                opp_id = None

        open_positions.append(
            _map_kalshi_position(
                kalshi_pos=kalshi_pos,
                avg_entry=avg_entry,
                current_price=current_price,
                existing=existing,
                resolved_opportunity_id=opp_id,
            )
        )

    # Filter out positions already reconciled as closed — Kalshi API can lag
    # after a limit sell fills, causing closed positions to reappear here.
    already_closed_keys = {
        (pos.market_ticker, pos.side)
        for pos in existing_state.closed_positions
    }
    pre_filter_count = len(open_positions)
    open_positions = [
        p for p in open_positions
        if (p.market_ticker, p.side) not in already_closed_keys
    ]
    filtered = pre_filter_count - len(open_positions)
    if filtered > 0:
        logger.warning(
            "Filtered %d already-closed position(s) from Kalshi sync (Kalshi API lag)",
            filtered,
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
    logger.info(
        "Synced portfolio: cash=$%.2f positions=%d",
        cash_balance,
        len(open_positions),
    )
    return new_state
