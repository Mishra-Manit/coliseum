"""Production pipeline orchestration: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""

import logging
from datetime import datetime, timezone

import logfire

from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian import run_guardian
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import Settings
from coliseum.memory.journal import JournalCycleSummary, write_journal_entry
from coliseum.storage.files import find_opportunity_file_by_id, mark_opportunity_failed
from coliseum.storage.state import load_state

logger = logging.getLogger("coliseum.pipeline")


async def run_pipeline(settings: Settings) -> JournalCycleSummary:
    """Run one full pipeline cycle: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""
    cycle_start = datetime.now(timezone.utc)
    summary = JournalCycleSummary(cycle_timestamp=cycle_start)
    errors: list[str] = []

    with logfire.span("pipeline cycle"):
        # Step 1: Guardian (pre-trade)
        with logfire.span("guardian pre-trade"):
            try:
                guardian_result = await run_guardian(settings=settings)
                summary.guardian_summary = (
                    f"Synced {guardian_result.positions_synced} positions, "
                    f"closed {guardian_result.reconciliation.newly_closed}"
                )
                logfire.info(
                    "Guardian complete",
                    synced=guardian_result.positions_synced,
                    closed=guardian_result.reconciliation.newly_closed,
                )
            except Exception as e:
                errors.append(f"Guardian: {e}")
                logfire.error("Guardian failed", error=str(e))

        # Pre-trade cash gate: skip Scout/Analyst/Trader if we can't afford to trade
        # In paper mode, bypass the cash check since no real funds are at risk
        if not settings.trading.paper_mode:
            min_cash = settings.trading.contracts * 1.0  # Need at least $1 per contract
            try:
                state = load_state()
                if state.portfolio.cash_balance < min_cash:
                    logfire.warn(
                        "Insufficient cash for trading cycle; skipping Scout/Analyst/Trader",
                        cash_balance=round(state.portfolio.cash_balance, 2),
                        min_cash_required=min_cash,
                    )
                    summary.scout_summary = "Skipped (insufficient cash)"
                    summary.analyst_summary = "N/A"
                    summary.trader_summary = "N/A"
                    _finalize_summary(summary, cycle_start, errors)
                    return summary
            except Exception as e:
                logger.warning("Could not load state for pre-trade cash check: %s", e)

        # Step 2: Scout
        with logfire.span("scout"):
            scout_output = await run_scout(settings=settings)

            if not scout_output or not scout_output.opportunities:
                summary.scout_summary = (
                    f"Scanned {scout_output.markets_scanned if scout_output else 0} markets, "
                    f"0 opportunities"
                )
                logfire.info("Scout found no opportunities")
                _finalize_summary(summary, cycle_start, errors)
                return summary

            opportunities = scout_output.opportunities
            total = len(opportunities)
            summary.scout_summary = (
                f"Scanned {scout_output.markets_scanned} markets, "
                f"{total} opportunities"
            )
            logfire.info("Scout complete", markets_scanned=scout_output.markets_scanned, opportunities=total)

        analyst_summaries: list[str] = []
        trader_summaries: list[str] = []

        # Step 3+4: For each opportunity, Analyst then Trader
        for i, opp in enumerate(opportunities, 1):
            with logfire.span("opportunity {ticker}", ticker=opp.market_ticker, opportunity_id=opp.id, index=i, total=total):
                with logfire.span("analyst", opportunity_id=opp.id):
                    try:
                        logger.info("Analyst starting for %s (%d/%d)", opp.market_ticker, i, total)
                        analyzed = await run_analyst(
                            opportunity_id=opp.id,
                            settings=settings,
                        )
                        analyst_summaries.append(f"{opp.market_ticker}: status={analyzed.status}")
                        logfire.info("Analyst complete", status=analyzed.status)
                        logger.info("Analyst complete for %s: status=%s", opp.market_ticker, analyzed.status)
                    except Exception as e:
                        errors.append(f"Analyst({opp.market_ticker}): {e}")
                        logfire.error("Analyst failed", error=str(e))
                        logger.error("Analyst failed for %s: %s", opp.market_ticker, e)
                        _mark_opportunity_failed(
                            opp.id,
                            settings.trading.paper_mode,
                            failed_stage="analyst",
                            error_message=str(e),
                        )
                        continue

                with logfire.span("trader", opportunity_id=opp.id):
                    try:
                        trader_output = await run_trader(
                            opportunity_id=opp.id,
                            settings=settings,
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
                        _mark_opportunity_failed(
                            opp.id,
                            settings.trading.paper_mode,
                            failed_stage="trader",
                            error_message=str(e),
                        )

        summary.analyst_summary = "; ".join(analyst_summaries) if analyst_summaries else "N/A"
        summary.trader_summary = "; ".join(trader_summaries) if trader_summaries else "N/A"

        logfire.info("All opportunities processed", count=total)

        # Step 5: Guardian (post-trade)
        with logfire.span("guardian post-trade"):
            try:
                guardian_result = await run_guardian(settings=settings)
                summary.guardian_summary += (
                    f" | Post-trade: synced {guardian_result.positions_synced}, "
                    f"closed {guardian_result.reconciliation.newly_closed}"
                )
                logfire.info(
                    "Guardian post-trade complete",
                    synced=guardian_result.positions_synced,
                    closed=guardian_result.reconciliation.newly_closed,
                )
            except Exception as e:
                errors.append(f"Guardian(post-trade): {e}")
                logfire.error("Guardian post-trade failed", error=str(e))

    _finalize_summary(summary, cycle_start, errors)
    return summary


def _mark_opportunity_failed(
    opportunity_id: str,
    paper: bool,
    *,
    failed_stage: str,
    error_message: str,
) -> None:
    """Set explicit failure metadata after an agent exception without changing body content."""
    try:
        opp_file = find_opportunity_file_by_id(opportunity_id, paper=paper)
        if opp_file:
            mark_opportunity_failed(
                opp_file,
                failed_stage=failed_stage,
                error_message=error_message,
            )
            logfire.info(
                "Opportunity marked failed",
                opportunity_id=opportunity_id,
                failed_stage=failed_stage,
            )
    except Exception as e:
        logger.error("Could not mark opportunity failed: %s", e)


def _finalize_summary(
    summary: JournalCycleSummary,
    cycle_start: datetime,
    errors: list[str],
) -> None:
    """Populate portfolio snapshot, duration, errors, and write the journal entry."""
    summary.duration_seconds = (datetime.now(timezone.utc) - cycle_start).total_seconds()
    summary.errors = errors

    try:
        state = load_state()
        summary.portfolio_cash = state.portfolio.cash_balance
        summary.portfolio_positions_value = state.portfolio.positions_value
        summary.portfolio_total = state.portfolio.total_value
        summary.open_position_count = len(state.open_positions)
    except Exception as e:
        logger.warning("Could not load portfolio state for journal: %s", e)

    try:
        write_journal_entry(summary)
    except Exception as e:
        logger.error("Failed to write journal entry: %s", e)
