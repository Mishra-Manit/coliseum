"""Recommender Agent: Trade decision making based on research."""

import logging
import time
from datetime import datetime, timezone

import logfire
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.analyst.models import AnalystDependencies, RecommenderOutput
from coliseum.agents.analyst.prompts import RECOMMENDER_PROMPT
from coliseum.memory.context import load_kalshi_mechanics
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_opportunity,
)
from coliseum.config import Settings
from coliseum.memory.context import build_analyst_context
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    get_opportunity_markdown_body,
    load_opportunity_from_file,
    update_opportunity_frontmatter,
)

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[AnalystDependencies, RecommenderOutput]:
    mechanics = load_kalshi_mechanics()
    system_prompt = f"{mechanics}\n\n{RECOMMENDER_PROMPT}"
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_4),
        output_type=RecommenderOutput,
        deps_type=AnalystDependencies,
        system_prompt=system_prompt,
        model_settings=OpenAIResponsesModelSettings(openai_reasoning_effort="low"),
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

    opp_file, opportunity = load_opportunity(opportunity_id, paper=settings.trading.paper_mode)

    if not opportunity.research_completed_at:
        raise ValueError(f"Research not completed for {opportunity_id}")

    markdown_body = get_opportunity_markdown_body(opp_file)

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    prompt = _build_decision_prompt(opportunity, markdown_body)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    update_opportunity_frontmatter(
        opp_file,
        {
            "recommendation_completed_at": completed_at.isoformat(),
            "action": None,
            "status": "recommended",
        },
    )

    logfire.info("Recommender complete", duration_seconds=round(duration, 1))

    updated_opp = load_opportunity_from_file(opp_file)
    return output, updated_opp


def _build_decision_prompt(
    opportunity: OpportunitySignal, markdown_body: str
) -> str:
    """Build the evaluation prompt for execution readiness."""
    header = format_opportunity_header(opportunity)
    memory_context = build_analyst_context()

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
