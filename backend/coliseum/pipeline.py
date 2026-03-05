"""Production pipeline orchestration: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""

import logging
from datetime import datetime, timezone

from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian import run_guardian
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import Settings
from coliseum.memory.journal import JournalCycleSummary, write_journal_entry
from coliseum.storage.state import load_state

logger = logging.getLogger("coliseum.pipeline")


async def run_pipeline(settings: Settings) -> JournalCycleSummary:
    """Run one full pipeline cycle: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""
    logger.info("Pipeline starting: Guardian -> Scout -> (Analyst -> Trader) -> Guardian")

    cycle_start = datetime.now(timezone.utc)
    summary = JournalCycleSummary(cycle_timestamp=cycle_start)
    errors: list[str] = []

    # Step 1: Guardian
    try:
        guardian_result = await run_guardian(settings=settings)
        summary.guardian_summary = (
            f"Synced {guardian_result.positions_synced} positions, "
            f"closed {guardian_result.reconciliation.newly_closed}"
        )
        logger.info(
            "Guardian complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        errors.append(f"Guardian: {e}")
        logger.error(f"Guardian failed: {e}")

    # Step 2: Scout
    scout_output = await run_scout(settings=settings)

    if not scout_output or not scout_output.opportunities:
        summary.scout_summary = (
            f"Scanned {scout_output.markets_scanned if scout_output else 0} markets, "
            f"0 opportunities"
        )
        logger.info("Scout found no opportunities. Pipeline complete.")
        _finalize_summary(summary, cycle_start, errors)
        return summary

    opportunities = scout_output.opportunities
    total = len(opportunities)
    summary.scout_summary = (
        f"Scanned {scout_output.markets_scanned} markets, "
        f"{total} opportunities"
    )
    logger.info(f"Scout found {total} opportunities")

    analyst_summaries: list[str] = []
    trader_summaries: list[str] = []

    # Step 3+4: For each opportunity, Analyst then Trader
    for i, opp in enumerate(opportunities, 1):
        logger.info(f"Processing opportunity {i}/{total}: {opp.market_ticker}")

        try:
            analyzed = await run_analyst(
                opportunity_id=opp.id,
                settings=settings,
            )
            analyst_summaries.append(f"{opp.market_ticker}: status={analyzed.status}")
            logger.info(f"Analyst complete for {opp.id}: status={analyzed.status}")
        except Exception as e:
            errors.append(f"Analyst({opp.market_ticker}): {e}")
            logger.error(f"Analyst failed for {opp.id}: {e}")
            continue

        try:
            trader_output = await run_trader(
                opportunity_id=opp.id,
                settings=settings,
            )
            trader_summaries.append(
                f"{opp.market_ticker}: {trader_output.decision.action} "
                f"({trader_output.execution_status})"
            )
            logger.info(
                f"Trader complete for {opp.id}: "
                f"decision={trader_output.decision.action} "
                f"status={trader_output.execution_status}"
            )
        except Exception as e:
            errors.append(f"Trader({opp.market_ticker}): {e}")
            logger.error(f"Trader failed for {opp.id}: {e}")

    summary.analyst_summary = "; ".join(analyst_summaries) if analyst_summaries else "N/A"
    summary.trader_summary = "; ".join(trader_summaries) if trader_summaries else "N/A"

    logger.info(f"Pipeline complete. Processed {total} opportunities.")

    # Step 5: Guardian (post-trade)
    try:
        guardian_result = await run_guardian(settings=settings)
        summary.guardian_summary += (
            f" | Post-trade: synced {guardian_result.positions_synced}, "
            f"closed {guardian_result.reconciliation.newly_closed}"
        )
        logger.info(
            "Guardian (post-trade) complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        errors.append(f"Guardian(post-trade): {e}")
        logger.error("Guardian (post-trade) failed: %s", e)

    _finalize_summary(summary, cycle_start, errors)
    return summary


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
