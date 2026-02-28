"""Guardian: deterministic portfolio reconciler (no LLM)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from coliseum.config import Settings, get_settings
from coliseum.services.kalshi import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.state import ClosedPosition, PortfolioState, Position, load_state, save_state
from coliseum.storage.sync import (
    extract_fill_count,
    extract_fill_price,
    fetch_market_side_price,
    normalize_kalshi_side,
    sync_portfolio_from_kalshi,
)

from .models import GuardianResult, ReconciliationStats

logger = logging.getLogger(__name__)


def _get_sell_fill_prices(
    fills: list[dict[str, object]],
    market_ticker: str,
    side: str,
) -> list[tuple[float, int]]:
    """Extract sell fill prices for a specific market and side."""
    prices: list[tuple[float, int]] = []
    for fill in fills:
        ticker = fill.get("ticker") or fill.get("market_ticker")
        if ticker != market_ticker:
            continue
        fill_side = normalize_kalshi_side(str(fill.get("side")) if fill.get("side") else None)
        if fill_side != side:
            continue
        action = fill.get("action")
        if action and str(action).lower() not in {"sell", "s"}:
            continue
        count = extract_fill_count(fill)
        if not count:
            continue
        price = extract_fill_price(fill, side)
        if price is None:
            continue
        prices.append((price, count))
    return prices


def _weighted_average(prices: list[tuple[float, int]]) -> float | None:
    """Compute weighted average price from (price, count) pairs."""
    if not prices:
        return None
    total_cost = sum(price * count for price, count in prices)
    total_count = sum(count for _, count in prices)
    if total_count <= 0:
        return None
    return total_cost / total_count


async def _fetch_market_price(
    client: KalshiClient,
    market_ticker: str,
    side: str,
) -> float | None:
    """Fetch current market price as a fallback for exit price."""
    try:
        return await fetch_market_side_price(client, market_ticker, side)
    except Exception as exc:
        logger.warning("Guardian failed to fetch market for %s: %s", market_ticker, exc)
        return None


async def _compute_exit_outcome(
    pos: Position,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[float, float]:
    """Return (exit_price, pnl) for a position that closed."""
    side = pos.side
    contracts = pos.contracts
    entry_price = pos.average_entry

    exit_prices = _get_sell_fill_prices(fills, pos.market_ticker, side)
    exit_price = _weighted_average(exit_prices)

    if exit_price is None:
        exit_price = await _fetch_market_price(client, pos.market_ticker, side)
        if exit_price is None:
            exit_price = entry_price
            logger.warning("Guardian using entry price as estimate for %s", pos.market_ticker)
        else:
            logger.warning("Guardian using market price estimate for %s", pos.market_ticker)

    if side == "YES":
        pnl = (exit_price - entry_price) * contracts
    else:
        pnl = (entry_price - exit_price) * contracts

    return exit_price, pnl


async def reconcile_closed_positions(
    old_open: list[Position],
    new_state: PortfolioState,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[PortfolioState, ReconciliationStats]:
    """Detect positions that closed since last sync and move them to closed_positions."""
    new_open_keys = {(pos.market_ticker, pos.side) for pos in new_state.open_positions}
    stats = ReconciliationStats()
    newly_closed: list[ClosedPosition] = []

    for pos in old_open:
        stats.entries_inspected += 1
        key = (pos.market_ticker, pos.side)
        if key in new_open_keys:
            stats.kept_open += 1
            continue

        exit_price, pnl = await _compute_exit_outcome(pos, fills, client)
        newly_closed.append(
            ClosedPosition(
                market_ticker=pos.market_ticker,
                side=pos.side,
                contracts=pos.contracts,
                entry_price=pos.average_entry,
                exit_price=exit_price,
                pnl=pnl,
                opportunity_id=pos.opportunity_id,
                closed_at=datetime.now(timezone.utc),
            )
        )
        stats.newly_closed += 1
        logger.info(
            "Guardian closed %s exit_price=%.4f pnl=$%.2f",
            pos.market_ticker,
            exit_price,
            pnl,
        )

    updated_state = PortfolioState(
        portfolio=new_state.portfolio,
        open_positions=new_state.open_positions,
        closed_positions=new_state.closed_positions + newly_closed,
        seen_tickers=new_state.seen_tickers,
    )
    save_state(updated_state)
    return updated_state, stats


def _find_positions_without_opportunity_id(state: PortfolioState) -> list[str]:
    """Find open positions that have no opportunity_id (not opened by our pipeline)."""
    return [
        f"{pos.market_ticker}:{pos.side}"
        for pos in state.open_positions
        if not pos.opportunity_id
    ]


async def run_guardian(settings: Settings | None = None) -> GuardianResult:
    """Run one Guardian reconciliation cycle: sync, reconcile, summarize."""
    settings = settings or get_settings()

    if settings.trading.paper_mode and not settings.get_rsa_private_key():
        logger.warning("Guardian skipped -- no real Kalshi data")
        return GuardianResult(agent_summary="Guardian skipped due to missing Kalshi auth.")

    kalshi_config = KalshiConfig(paper_mode=settings.trading.paper_mode)
    private_key_pem = "" if settings.trading.paper_mode else settings.get_rsa_private_key()

    async with KalshiClient(
        config=kalshi_config,
        api_key=settings.kalshi_api_key,
        private_key_pem=private_key_pem,
    ) as client:
        # Step 1: snapshot pre-sync positions
        pre_sync_state = load_state()

        # Step 2: sync portfolio from Kalshi (updates state.yaml with balances + positions)
        state = await sync_portfolio_from_kalshi(client)
        logger.info(
            "Guardian synced portfolio: cash=$%.2f positions_value=$%.2f total=$%.2f open=%d",
            state.portfolio.cash_balance,
            state.portfolio.positions_value,
            state.portfolio.total_value,
            len(state.open_positions),
        )

        # Step 3: fetch recent fills for exit price calculation
        fills = await client.get_fills(limit=500)

        # Step 4: reconcile closed positions
        updated_state, stats = await reconcile_closed_positions(
            old_open=pre_sync_state.open_positions,
            new_state=state,
            fills=fills,
            client=client,
        )

        # Step 5: find positions not opened by our pipeline
        missing = _find_positions_without_opportunity_id(updated_state)

    for missing_key in missing:
        logger.warning("Guardian position missing opportunity_id: %s", missing_key)

    logger.info("Guardian synced %d positions from Kalshi", len(updated_state.open_positions))
    logger.info(
        "Guardian reconciliation: inspected=%d kept_open=%d closed=%d",
        stats.entries_inspected,
        stats.kept_open,
        stats.newly_closed,
    )

    return GuardianResult(
        positions_synced=len(updated_state.open_positions),
        reconciliation=stats,
        warnings=missing,
        agent_summary=(
            f"Synced {len(updated_state.open_positions)} positions. "
            f"Reconciled {stats.newly_closed} closed. "
            f"{len(missing)} missing opportunity_id."
        ),
    )


def guardian_job() -> None:
    """Scheduler job wrapper for Guardian reconciliation."""
    try:
        result = asyncio.run(run_guardian())
        logger.info(
            "Guardian: %d positions synced, %d closed",
            result.positions_synced,
            result.reconciliation.newly_closed,
        )
    except Exception as exc:
        logger.error("Guardian run failed: %s", exc, exc_info=True)
