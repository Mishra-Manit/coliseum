"""Analyst Agent: Orchestration layer for Researcher + Recommender pipeline.

This module orchestrates the two-agent pipeline:
- Researcher: Conducts research, appends to opportunity file
- Recommender: Makes trade decisions based on research, appends recommendation

All stages write to a single opportunity file.
"""

import logging

import logfire

from coliseum.agents.analyst.recommender import run_recommender
from coliseum.agents.analyst.researcher import run_researcher
from coliseum.config import Settings
from coliseum.domain.opportunity import OpportunitySignal

logger = logging.getLogger(__name__)



async def run_analyst(
    opportunity_id: str,
    settings: Settings,
) -> OpportunitySignal:
    """Run full Analyst pipeline: Researcher + Recommender.

    This is the main entry point that orchestrates both agents sequentially:
    1. Researcher conducts research and appends to opportunity file
    2. Recommender evaluates research and appends recommendation
    """
    logger.info("Analyst starting: %s", opportunity_id)
    with logfire.span("analyst pipeline", opportunity_id=opportunity_id):
        with logfire.span("researcher", opportunity_id=opportunity_id):
            logger.info("Researcher starting")
            await run_researcher(
                opportunity_id=opportunity_id,
                settings=settings,
            )
            logfire.info("Research complete")
            logger.info("Researcher complete")

        with logfire.span("recommender", opportunity_id=opportunity_id):
            logger.info("Recommender starting")
            _, opportunity = await run_recommender(
                opportunity_id=opportunity_id,
                settings=settings,
            )
            logfire.info("Recommendation complete")
            logger.info("Recommender complete: status=%s", opportunity.status)

    logger.info("Analyst complete: %s status=%s", opportunity_id, opportunity.status)
    return opportunity
