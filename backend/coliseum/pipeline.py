"""Production pipeline orchestration: Scout -> (Analyst -> Trader)."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ParamSpec, TypeVar

import logfire

from coliseum.agents.analyst import run_analyst
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import Settings
from coliseum.memory.journal import JournalCycleSummary
from coliseum.services.supabase.repositories.opportunities import mark_opportunity_failed_in_db
from coliseum.services.supabase.repositories.portfolio import load_state_from_db
from coliseum.services.supabase.repositories.run_cycles import save_run_cycle_to_db


@dataclass
class CycleMetrics:
    """Structured metrics collected during a pipeline cycle for DB persistence."""

    scout_scanned: int = 0
    scout_found: int = 0
    analyst_results: dict[str, str] = field(default_factory=dict)
    trader_results: dict[str, str] = field(default_factory=dict)

logger = logging.getLogger("coliseum.pipeline")

P = ParamSpec("P")
T = TypeVar("T")

_TRANSIENT_MARKERS = ("status_code: 500", "status_code: 502", "status_code: 503", "status_code: 429", "temporarily unavailable", "rate limit")


async def _retry_transient(
    fn: Callable[P, Awaitable[T]],
    *args: P.args,
    _max_retries: int = 2,
    _base_delay: float = 5.0,
    **kwargs: P.kwargs,
) -> T:
    """Call fn with retries on transient provider errors (500/502/503/429)."""
    for attempt in range(_max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            lowered = str(exc).lower()
            is_transient = any(m in lowered for m in _TRANSIENT_MARKERS)
            if not is_transient or attempt == _max_retries:
                raise
            delay = _base_delay * (2 ** attempt)
            logger.warning("Transient error (attempt %d/%d), retrying in %.0fs: %s", attempt + 1, _max_retries, delay, exc)
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")


def _shutdown_requested(shutdown_event: asyncio.Event | None) -> bool:
    """Check if a graceful shutdown has been requested."""
    return shutdown_event is not None and shutdown_event.is_set()


async def run_pipeline(settings: Settings, shutdown_event: asyncio.Event | None = None) -> JournalCycleSummary:
    """Run one full pipeline cycle: Scout -> (Analyst -> Trader)."""
    cycle_start = datetime.now(timezone.utc)
    summary = JournalCycleSummary(cycle_timestamp=cycle_start)
    metrics = CycleMetrics()
    errors: list[str] = []

    with logfire.span("pipeline cycle"):
        # Pre-trade cash gate: skip Scout/Analyst/Trader if we can't afford to trade
        # In paper mode, bypass the cash check since no real funds are at risk
        if not settings.trading.paper_mode:
            min_cash = settings.trading.contracts * 1.0  # Need at least $1 per contract
            try:
                state = await load_state_from_db()
                if state.portfolio.cash_balance < min_cash:
                    logfire.warn(
                        "Insufficient cash for trading cycle; skipping Scout/Analyst/Trader",
                        cash_balance=round(state.portfolio.cash_balance, 2),
                        min_cash_required=min_cash,
                    )
                    summary.scout_summary = "Skipped (insufficient cash)"
                    summary.analyst_summary = "N/A"
                    summary.trader_summary = "N/A"
                    await _finalize_summary(summary, cycle_start, errors, metrics)
                    return summary
            except Exception as e:
                logger.warning("Could not load state for pre-trade cash check: %s", e)

        # Step 2: Scout
        with logfire.span("scout"):
            try:
                scout_output = await run_scout(settings=settings)
            except Exception as e:
                errors.append(f"Scout: {e}")
                logfire.error("Scout failed", error=str(e))
                summary.scout_summary = f"Failed: {e}"
                await _finalize_summary(summary, cycle_start, errors, metrics)
                return summary

            if not scout_output or not scout_output.opportunities:
                if scout_output:
                    metrics.scout_scanned = scout_output.markets_scanned
                else:
                    metrics.scout_scanned = 0

                summary.scout_summary = (
                    f"Scanned {metrics.scout_scanned} markets, "
                    f"0 opportunities"
                )
                logfire.info("Scout found no opportunities")
                await _finalize_summary(summary, cycle_start, errors, metrics)
                return summary

            opportunities = scout_output.opportunities
            total = len(opportunities)
            metrics.scout_scanned = scout_output.markets_scanned
            metrics.scout_found = total
            summary.scout_summary = (
                f"Scanned {scout_output.markets_scanned} markets, "
                f"{total} opportunities"
            )
            logfire.info("Scout complete", markets_scanned=scout_output.markets_scanned, opportunities=total)

        if _shutdown_requested(shutdown_event):
            logger.info("Shutdown requested after Scout, exiting pipeline")
            summary.analyst_summary = "Skipped (shutdown)"
            summary.trader_summary = "Skipped (shutdown)"
            await _finalize_summary(summary, cycle_start, errors, metrics)
            return summary

        analyst_summaries: list[str] = []
        trader_summaries: list[str] = []

        # Step 3+4: For each opportunity, Analyst then Trader
        for i, opp in enumerate(opportunities, 1):
            if _shutdown_requested(shutdown_event):
                logger.info(
                    "Shutdown requested, skipping remaining %d/%d opportunities",
                    total - i + 1,
                    total,
                )
                break

            with logfire.span("opportunity {ticker}", ticker=opp.market_ticker, opportunity_id=opp.id, index=i, total=total):
                with logfire.span("analyst", opportunity_id=opp.id):
                    try:
                        logger.info("Analyst starting for %s (%d/%d)", opp.market_ticker, i, total)
                        analyzed = await _retry_transient(
                            run_analyst,
                            opportunity_id=opp.id,
                            settings=settings,
                        )
                        metrics.analyst_results[opp.market_ticker] = analyzed.status
                        analyst_summaries.append(f"{opp.market_ticker}: status={analyzed.status}")
                        logfire.info("Analyst complete", status=analyzed.status)
                        logger.info("Analyst complete for %s: status=%s", opp.market_ticker, analyzed.status)
                    except Exception as e:
                        errors.append(f"Analyst({opp.market_ticker}): {e}")
                        logfire.error("Analyst failed", error=str(e))
                        logger.error("Analyst failed for %s: %s", opp.market_ticker, e)
                        await _mark_opportunity_failed(
                            opp.id,
                            failed_stage="analyst",
                            error_message=str(e),
                        )
                        continue

                if _shutdown_requested(shutdown_event):
                    logger.info("Shutdown requested after Analyst for %s, skipping Trader", opp.market_ticker)
                    break

                with logfire.span("trader", opportunity_id=opp.id):
                    try:
                        trader_output = await _retry_transient(
                            run_trader,
                            opportunity_id=opp.id,
                            settings=settings,
                            shutdown_event=shutdown_event,
                        )
                        metrics.trader_results[opp.market_ticker] = (
                            f"{trader_output.decision.action} ({trader_output.execution_status})"
                        )
                        trader_summaries.append(
                            f"{opp.market_ticker}: {trader_output.decision.action} "
                            f"({trader_output.execution_status})"
                        )
                        logfire.info(
                            "Trader complete",
                            decision=trader_output.decision.action,
                            status=trader_output.execution_status,
                        )
                    except Exception as e:
                        errors.append(f"Trader({opp.market_ticker}): {e}")
                        logfire.error("Trader failed", error=str(e))
                        await _mark_opportunity_failed(
                            opp.id,
                            failed_stage="trader",
                            error_message=str(e),
                        )

        if analyst_summaries:
            summary.analyst_summary = "; ".join(analyst_summaries)
        else:
            summary.analyst_summary = "N/A"

        if trader_summaries:
            summary.trader_summary = "; ".join(trader_summaries)
        else:
            summary.trader_summary = "N/A"

        logfire.info("All opportunities processed", count=total)

    await _finalize_summary(summary, cycle_start, errors, metrics)
    return summary


async def _mark_opportunity_failed(
    opportunity_id: str,
    *,
    failed_stage: str,
    error_message: str,
) -> None:
    """Set explicit failure metadata after an agent exception without changing body content."""
    try:
        await mark_opportunity_failed_in_db(
            opportunity_id=opportunity_id,
            failed_stage=failed_stage,
            error_message=error_message,
        )
    except Exception as e:
        logfire.error("DB mark-failed write failed", opportunity_id=opportunity_id, error=str(e))


async def _finalize_summary(
    summary: JournalCycleSummary,
    cycle_start: datetime,
    errors: list[str],
    metrics: CycleMetrics,
) -> None:
    """Populate cycle summary fields and persist pipeline telemetry."""
    summary.duration_seconds = (datetime.now(timezone.utc) - cycle_start).total_seconds()
    summary.errors = errors

    try:
        state = await load_state_from_db()
        summary.portfolio_cash = state.portfolio.cash_balance
        summary.portfolio_positions_value = state.portfolio.positions_value
        summary.portfolio_total = state.portfolio.total_value
        summary.open_position_count = len(state.open_positions)
    except Exception as e:
        logger.warning("Could not load portfolio state for journal: %s", e)

    # DB write first (primary)
    try:
        await save_run_cycle_to_db(
            cycle_at=summary.cycle_timestamp,
            duration_seconds=summary.duration_seconds,
            scout_scanned=metrics.scout_scanned,
            scout_found=metrics.scout_found,
            analyst_results=metrics.analyst_results if metrics.analyst_results else None,
            trader_results=metrics.trader_results if metrics.trader_results else None,
            cash_balance=summary.portfolio_cash,
            positions_value=summary.portfolio_positions_value,
            total_value=summary.portfolio_total,
            open_positions=summary.open_position_count,
            errors=summary.errors,
        )
    except Exception as e:
        logfire.error("Failed to write run_cycle to DB", error=str(e))
