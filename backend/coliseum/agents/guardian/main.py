"""Guardian: deterministic portfolio reconciler with LLM-powered learning reflection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import logfire

from coliseum.config import Settings, get_settings
from coliseum.services.kalshi import KalshiClient
from coliseum.services.telegram import TelegramClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.storage.files import (
    TradeClose,
    find_opportunity_file_by_id,
    generate_close_id,
    get_opportunity_markdown_body,
    log_trade_close,
)
from coliseum.storage.state import ClosedPosition, PortfolioState, Position, load_state, save_state
from coliseum.storage.sync import (
    extract_fill_count,
    extract_fill_price,
    fetch_market_side_price,
    normalize_kalshi_side,
    resolve_market_price,
    sync_portfolio_from_kalshi,
)

from .models import GuardianResult, ReconciliationStats
from .scribe import run_scribe

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

    pnl = round((exit_price - entry_price) * contracts, 4)

    return exit_price, pnl


def _extract_entry_rationale(opportunity_id: str | None) -> str | None:
    """Read opportunity file and extract the original Scout rationale."""
    if not opportunity_id:
        return None
    try:
        opp_file = find_opportunity_file_by_id(opportunity_id)
        if not opp_file:
            return None
        body = get_opportunity_markdown_body(opp_file)
        for line in body.splitlines():
            if line.startswith("**Rationale**:"):
                return line.removeprefix("**Rationale**:").strip()
        return None
    except Exception as exc:
        logger.warning("Could not extract entry rationale for %s: %s", opportunity_id, exc)
        return None


async def execute_stop_loss_exits(
    state: PortfolioState,
    client: KalshiClient,
    settings: Settings,
) -> list[str]:
    """Sell any open position whose current_price is below the stop-loss threshold."""
    threshold = settings.guardian.stop_loss_price
    triggered: list[str] = []

    for pos in state.open_positions:
        if pos.current_price >= threshold:
            continue

        open_orders = await client.get_orders(ticker=pos.market_ticker, status="resting")
        if any(o.action == "sell" for o in open_orders):
            logger.info("Stop-loss sell already pending for %s", pos.market_ticker)
            continue

        side_lower = pos.side.lower()
        sell_price = int(pos.current_price * 100)

        try:
            if side_lower == "yes":
                await client.place_order(
                    ticker=pos.market_ticker,
                    side="yes",
                    action="sell",
                    count=pos.contracts,
                    yes_price=sell_price,
                )
            else:
                await client.place_order(
                    ticker=pos.market_ticker,
                    side="no",
                    action="sell",
                    count=pos.contracts,
                    no_price=sell_price,
                )
            triggered.append(pos.market_ticker)
            logfire.info(
                "Stop-loss triggered",
                ticker=pos.market_ticker,
                current_price=pos.current_price,
                threshold=threshold,
                sell_price_cents=sell_price,
            )
            if settings.telegram_send_alerts and settings.telegram_bot_token:
                try:
                    msg = (
                        f"STOP-LOSS TRIGGERED\n\n"
                        f"Ticker: {pos.market_ticker}\n"
                        f"Side: {pos.side}\n"
                        f"Contracts: {pos.contracts}\n"
                        f"Current Price: {pos.current_price:.2f}\n"
                        f"Sell At: {sell_price}¢\n"
                        f"Threshold: {threshold:.2f}"
                    )
                    async with TelegramClient(
                        bot_token=settings.telegram_bot_token,
                        default_chat_id=settings.telegram_chat_id,
                    ) as tg:
                        await tg.send_alert(msg)
                except Exception as tg_exc:
                    logger.warning("Stop-loss Telegram alert failed (non-fatal): %s", tg_exc)
        except Exception as exc:
            logger.error("Stop-loss sell failed for %s: %s", pos.market_ticker, exc)

    return triggered


async def reconcile_closed_positions(
    old_open: list[Position],
    new_state: PortfolioState,
    fills: list[dict[str, object]],
    client: KalshiClient,
) -> tuple[PortfolioState, ReconciliationStats, list[ClosedPosition]]:
    """Detect positions that closed since last sync and move them to closed_positions."""
    new_open_keys = {(pos.market_ticker, pos.side) for pos in new_state.open_positions}
    already_closed_keys = {(pos.market_ticker, pos.side) for pos in new_state.closed_positions}
    stats = ReconciliationStats()
    newly_closed: list[ClosedPosition] = []

    pending_keeps: list[Position] = []

    for pos in old_open:
        stats.entries_inspected += 1
        key = (pos.market_ticker, pos.side)
        if key in new_open_keys:
            stats.kept_open += 1
            continue
        if key in already_closed_keys:
            logger.warning(
                "Guardian skipping %s: already reconciled as closed in a prior run",
                pos.market_ticker,
            )
            stats.duplicate_close_skipped += 1
            continue

        try:
            market = await client.get_market(pos.market_ticker)
            if market.status == "closed":
                fresh_price = resolve_market_price(market, pos.side) or pos.current_price
                pending_keeps.append(Position(
                    id=pos.id,
                    market_ticker=pos.market_ticker,
                    side=pos.side,
                    contracts=pos.contracts,
                    average_entry=pos.average_entry,
                    current_price=fresh_price,
                    opportunity_id=pos.opportunity_id,
                ))
                stats.kept_open += 1
                logger.info(
                    "Guardian holding %s: market closed pending settlement",
                    pos.market_ticker,
                )
                continue
        except Exception as exc:
            logger.warning(
                "Guardian could not verify market status for %s, holding: %s",
                pos.market_ticker,
                exc,
            )
            pending_keeps.append(pos)
            stats.kept_open += 1
            continue

        closed_at = datetime.now(timezone.utc)
        exit_price, pnl = await _compute_exit_outcome(pos, fills, client)
        entry_rationale = _extract_entry_rationale(pos.opportunity_id)

        closed_pos = ClosedPosition(
            market_ticker=pos.market_ticker,
            side=pos.side,
            contracts=pos.contracts,
            entry_price=pos.average_entry,
            exit_price=exit_price,
            pnl=pnl,
            opportunity_id=pos.opportunity_id,
            closed_at=closed_at,
            entry_rationale=entry_rationale,
        )
        newly_closed.append(closed_pos)

        log_trade_close(
            TradeClose(
                id=generate_close_id(),
                opportunity_id=pos.opportunity_id,
                market_ticker=pos.market_ticker,
                side=pos.side,
                contracts=pos.contracts,
                entry_price=pos.average_entry,
                exit_price=exit_price,
                pnl=pnl,
                entry_rationale=entry_rationale,
                closed_at=closed_at,
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
        open_positions=new_state.open_positions + pending_keeps,
        closed_positions=new_state.closed_positions + newly_closed,
        seen_tickers=new_state.seen_tickers,
    )
    save_state(updated_state)
    return updated_state, stats, newly_closed


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

    if settings.trading.paper_mode:
        logger.info("Guardian skipped in paper mode (no real positions to reconcile)")
        return GuardianResult(agent_summary="Guardian skipped in paper mode.")

    kalshi_config = KalshiConfig()
    private_key_pem = settings.get_rsa_private_key()

    with logfire.span("guardian reconciliation"):
        async with KalshiClient(
            config=kalshi_config,
            api_key=settings.kalshi_api_key,
            private_key_pem=private_key_pem,
        ) as client:
            # Step 1: snapshot pre-sync positions
            pre_sync_state = load_state()

            # Step 2: sync portfolio from Kalshi
            with logfire.span("sync portfolio from Kalshi"):
                state = await sync_portfolio_from_kalshi(client)
                logfire.info(
                    "Portfolio synced",
                    cash=round(state.portfolio.cash_balance, 2),
                    positions_value=round(state.portfolio.positions_value, 2),
                    total=round(state.portfolio.total_value, 2),
                    open_positions=len(state.open_positions),
                )

            # Step 3: execute stop-loss exits on positions below threshold
            with logfire.span("stop loss check"):
                stop_loss_tickers = await execute_stop_loss_exits(state, client, settings)
                if stop_loss_tickers:
                    logfire.info("Stop-loss exits placed", tickers=stop_loss_tickers)

            # Step 4: fetch recent fills for exit price calculation
            with logfire.span("fetch fills"):
                fills = await client.get_fills(limit=500)
                logfire.info("Fills fetched", count=len(fills))

            # Re-sync after stop-loss sells so reconciliation sees the position as gone
            if stop_loss_tickers:
                with logfire.span("re-sync after stop loss"):
                    state = await sync_portfolio_from_kalshi(client)
                    logfire.info(
                        "Re-synced after stop-loss",
                        open_positions=len(state.open_positions),
                    )

            # Step 5: reconcile closed positions
            with logfire.span("reconcile closed positions", inspected=len(pre_sync_state.open_positions)):
                updated_state, stats, newly_closed = await reconcile_closed_positions(
                    old_open=pre_sync_state.open_positions,
                    new_state=state,
                    fills=fills,
                    client=client,
                )
                logfire.info(
                    "Reconciliation complete",
                    inspected=stats.entries_inspected,
                    kept_open=stats.kept_open,
                    newly_closed=stats.newly_closed,
                    duplicate_close_skipped=stats.duplicate_close_skipped,
                )

            # Step 6: find positions not opened by our pipeline
            missing = _find_positions_without_opportunity_id(updated_state)

        for missing_key in missing:
            logfire.warn("Position missing opportunity_id", position=missing_key)

        # Step 7: LLM reflection — update learnings when trades close
        if newly_closed:
            try:
                with logfire.span("scribe reflection", trades=len(newly_closed)):
                    scribe_summary = await run_scribe(newly_closed)
                    logfire.info("Scribe complete", summary=scribe_summary)
            except Exception as exc:
                logger.warning("Scribe reflection failed (non-fatal): %s", exc)

        logfire.info(
            "Guardian complete",
            positions_synced=len(updated_state.open_positions),
            newly_closed=stats.newly_closed,
            missing_opportunity_ids=len(missing),
        )

    return GuardianResult(
        positions_synced=len(updated_state.open_positions),
        reconciliation=ReconciliationStats(
            entries_inspected=stats.entries_inspected,
            kept_open=stats.kept_open,
            newly_closed=stats.newly_closed,
            duplicate_close_skipped=stats.duplicate_close_skipped,
            stop_loss_exits=len(stop_loss_tickers),
            warnings=stats.warnings,
        ),
        stop_loss_tickers=stop_loss_tickers,
        warnings=missing,
        agent_summary=(
            f"Synced {len(updated_state.open_positions)} positions. "
            f"Reconciled {stats.newly_closed} closed. "
            f"Stop-loss exits: {len(stop_loss_tickers)}. "
            f"{len(missing)} missing opportunity_id."
        ),
    )
