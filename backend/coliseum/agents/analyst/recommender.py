"""Recommender Agent: Trade decision making based on research."""

import logging
import time
from datetime import datetime, timezone

import logfire
from pydantic_ai import Agent

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.analyst.models import AnalystDependencies, RecommenderOutput
from coliseum.agents.analyst.prompts import RECOMMENDER_PROMPT
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_opportunity,
)
from coliseum.config import Settings
from coliseum.memory.context import build_analyst_context
from coliseum.services.supabase.repositories.opportunities import (
    get_opportunity_body_from_db,
    update_opportunity_recommendation,
)
from coliseum.storage.files import (
    OpportunitySignal,
    find_opportunity_file,
    update_opportunity_frontmatter,
)

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[AnalystDependencies, RecommenderOutput]:
    return create_agent(
        prompt=RECOMMENDER_PROMPT,
        output_type=RecommenderOutput,
        deps_type=AnalystDependencies,
        use_responses_api=False,
    )


_agent_factory = AgentFactory(create_fn=_create_agent)


def get_agent() -> Agent[AnalystDependencies, RecommenderOutput]:
    """Get the singleton Recommender agent instance."""
    return _agent_factory.get_agent()


async def run_recommender(
    opportunity_id: str,
    settings: Settings,
) -> tuple[RecommenderOutput, OpportunitySignal]:
    """Run Recommender agent - updates opportunity frontmatter with recommendation status."""
    start_time = time.time()

    opportunity = await load_opportunity(opportunity_id)

    if not opportunity.research_completed_at:
        raise ValueError(f"Research not completed for {opportunity_id}")

    markdown_body = await get_opportunity_body_from_db(opportunity.id)

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
    )
    prompt = await _build_decision_prompt(opportunity, markdown_body)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    try:
        await update_opportunity_recommendation(
            opportunity_id=opportunity_id,
            completed_at=completed_at,
            action=None,  # action is set later by the Trader agent
            status="recommended",
        )
    except Exception as e:
        logfire.error("DB write failed for recommender", opportunity_id=opportunity_id, error=str(e))

    opp_file = find_opportunity_file(opportunity.market_ticker, paper=settings.trading.paper_mode)
    if opp_file:
        update_opportunity_frontmatter(
            opp_file,
            {
                "recommendation_completed_at": completed_at.isoformat(),
                "action": None,
                "status": "recommended",
            },
        )

    logfire.info("Recommender complete", duration_seconds=round(duration, 1))

    updated_opp = await load_opportunity(opportunity.id)
    return output, updated_opp


async def _build_decision_prompt(
    opportunity: OpportunitySignal, markdown_body: str
) -> str:
    """Build the evaluation prompt for execution readiness."""
    header = format_opportunity_header(opportunity)
    memory_context = await build_analyst_context()

    return f"""Screen this research for execution readiness. Your output goes directly to the Trader.
{memory_context}
## Opportunity

{header}

## Research Output

{markdown_body}

## Pre-Screening Checklist

Work through each before writing your reasoning:

1. Flip risk verdict: YES / NO / UNCERTAIN?
2. If NO — does the researcher cite a specific named source confirming the outcome, or just report an absence of bad news?
3. Unconfirmed section: is it empty, or does it list material gaps?
4. Resolution mechanics: sourced explicitly, or assumed?
5. Portfolio context above: any open position in the same or correlated market?

Write your verdict (PROCEED / HOLD / REJECT), then your reasoning. Be specific — name the evidence, not the category.
"""
