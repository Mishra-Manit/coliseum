"""Analyst Agent: Orchestration layer for Researcher + Recommender pipeline.

This module orchestrates the two-agent pipeline:
- Researcher: Conducts research, appends to opportunity file
- Recommender: Makes trade decisions based on research, appends recommendation

All stages write to a single opportunity file.
"""

import logging

from coliseum.agents.analyst.recommender import run_recommender
from coliseum.agents.analyst.researcher import run_researcher
from coliseum.config import Settings
from coliseum.storage.files import OpportunitySignal

logger = logging.getLogger(__name__)


__all__ = [
    "run_analyst",
    "run_researcher",
    "run_recommender",
]


async def run_analyst(
    opportunity_id: str,
    settings: Settings,
) -> OpportunitySignal:
    """Run full Analyst pipeline: Researcher + Recommender.

    This is the main entry point that orchestrates both agents sequentially:
    1. Researcher conducts research and appends to opportunity file
    2. Recommender evaluates research and appends recommendation
    """
    logger.info(f"Running full Analyst pipeline for: {opportunity_id}")

    # Phase 1: Research
    logger.info("Phase 1: Running Researcher...")
    await run_researcher(
        opportunity_id=opportunity_id,
        settings=settings,
    )

    logger.info("Research complete")

    # Phase 2: Recommendation
    logger.info("Phase 2: Running Recommender...")
    _, opportunity = await run_recommender(
        opportunity_id=opportunity_id,
        settings=settings,
    )

    logger.info("Recommendation complete")

    return opportunity
