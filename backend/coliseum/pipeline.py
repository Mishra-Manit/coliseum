"""Production pipeline orchestration: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""

import logging

from coliseum.agents.analyst import run_analyst
from coliseum.agents.guardian import run_guardian
from coliseum.agents.scout import run_scout
from coliseum.agents.trader import run_trader
from coliseum.config import Settings

logger = logging.getLogger("coliseum.pipeline")


async def run_pipeline(settings: Settings) -> None:
    """Run one full pipeline cycle: Guardian -> Scout -> (Analyst -> Trader) -> Guardian."""
    logger.info("Pipeline starting: Guardian -> Scout -> (Analyst -> Trader) -> Guardian")

    # Step 1: Guardian
    try:
        guardian_result = await run_guardian(settings=settings)
        logger.info(
            "Guardian complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        logger.error(f"Guardian failed: {e}")

    # Step 2: Scout
    scout_output = await run_scout(strategy=settings.strategy)

    if not scout_output or not scout_output.opportunities:
        logger.info("Scout found no opportunities. Pipeline complete.")
        return

    opportunities = scout_output.opportunities
    total = len(opportunities)
    logger.info(f"Scout found {total} opportunities")

    # Step 3+4: For each opportunity, Analyst then Trader
    for i, opp in enumerate(opportunities, 1):
        logger.info(f"Processing opportunity {i}/{total}: {opp.market_ticker}")

        try:
            analyzed = await run_analyst(
                opportunity_id=opp.id,
                settings=settings,
            )
            logger.info(
                f"Analyst complete for {opp.id}: "
                f"edge={analyzed.edge:+.2%}" if analyzed.edge is not None
                else f"Analyst complete for {opp.id}: edge=N/A"
            )
        except Exception as e:
            logger.error(f"Analyst failed for {opp.id}: {e}")
            continue

        try:
            trader_output = await run_trader(
                opportunity_id=opp.id,
                settings=settings,
            )
            logger.info(
                f"Trader complete for {opp.id}: "
                f"decision={trader_output.decision.action} "
                f"status={trader_output.execution_status}"
            )
        except Exception as e:
            logger.error(f"Trader failed for {opp.id}: {e}")

    logger.info(f"Pipeline complete. Processed {total} opportunities.")

    # Step 5: Guardian (post-trade)
    try:
        guardian_result = await run_guardian(settings=settings)
        logger.info(
            "Guardian (post-trade) complete: synced=%d closed=%d",
            guardian_result.positions_synced,
            guardian_result.reconciliation.newly_closed,
        )
    except Exception as e:
        logger.error("Guardian (post-trade) failed: %s", e)
