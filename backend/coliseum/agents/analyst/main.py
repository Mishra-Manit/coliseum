"""Analyst Agent: Orchestration layer for Researcher + Recommender pipeline.

This module orchestrates the two-agent pipeline:
- Researcher: Conducts research, appends to opportunity file
- Recommender: Makes trade decisions based on research, appends recommendation

The original monolithic Analyst agent is split into specialized agents for improved
reliability and separation of concerns. All stages write to a single opportunity file.
"""

import logging

from coliseum.agents.analyst.recommender import run_recommender
from coliseum.agents.analyst.researcher import run_researcher
from coliseum.config import Settings
from coliseum.storage.files import OpportunitySignal

logger = logging.getLogger(__name__)


# Re-export for backward compatibility and convenience
__all__ = [
    "run_analyst",
    "run_researcher",
    "run_recommender",
]


async def run_analyst(
    opportunity_id: str,
    settings: Settings,
    dry_run: bool = False,
) -> OpportunitySignal:
    """Run full Analyst pipeline: Researcher + Recommender.

    This is the main entry point that orchestrates both agents sequentially:
    1. Researcher conducts research and appends to opportunity file
    2. Recommender evaluates research and appends recommendation

    Returns:
        Complete OpportunitySignal with all stages populated
    """
    logger.info(f"Running full Analyst pipeline for: {opportunity_id}")

    # Phase 1: Research
    logger.info("Phase 1: Running Researcher...")
    research_output = await run_researcher(
        opportunity_id=opportunity_id,
        settings=settings,
        dry_run=dry_run,
    )

    logger.info(
        f"Research complete - Sources: {research_output.sources_count}"
    )

    # Phase 2: Recommendation
    logger.info("Phase 2: Running Recommender...")
    recommendation_output, opportunity = await run_recommender(
        opportunity_id=opportunity_id,
        settings=settings,
        dry_run=dry_run,
    )

    logger.info(
        f"Recommendation complete - "
        f"Edge: {opportunity.edge:+.2%}, "
        f"EV: {opportunity.expected_value:+.2%}"
    )

    return opportunity
