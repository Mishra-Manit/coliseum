"""Recommender Agent: Trade decision making based on research."""

import logging
import time
from datetime import datetime, timezone

import logfire
from pydantic_ai import Agent

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.analyst.models import AnalystDependencies, RecommenderOutput
from coliseum.agents.analyst.prompts import RECOMMENDER_PROMPT
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_opportunity,
)
from coliseum.config import Settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    get_opportunity_markdown_body,
    load_opportunity_from_file,
)

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[AnalystDependencies, RecommenderOutput]:
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=RecommenderOutput,
        deps_type=AnalystDependencies,
        system_prompt=RECOMMENDER_PROMPT,
    )


_agent_factory = AgentFactory(create_fn=_create_agent)


def get_agent() -> Agent[AnalystDependencies, RecommenderOutput]:
    """Get the singleton Recommender agent instance."""
    return _agent_factory.get_agent()


async def run_recommender(
    opportunity_id: str,
    settings: Settings,
) -> tuple[RecommenderOutput, OpportunitySignal]:
    """Run Recommender agent - appends recommendation to opportunity file."""
    start_time = time.time()

    opp_file, opportunity = load_opportunity(opportunity_id)

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

    recommendation_section = f"""---

## Trade Evaluation

**Status**: Pending

### Reasoning

{output.reasoning}"""
    frontmatter_updates = {
        "recommendation_completed_at": completed_at.isoformat(),
        "action": None,
        "status": "recommended",
    }

    append_to_opportunity(
        market_ticker=opportunity.market_ticker,
        frontmatter_updates=frontmatter_updates,
        body_section=recommendation_section,
        section_header="## Trade Evaluation",
    )

    logfire.info("Recommender complete", duration_seconds=round(duration, 1))

    updated_opp = load_opportunity_from_file(opp_file)
    return output, updated_opp


def _build_decision_prompt(
    opportunity: OpportunitySignal, markdown_body: str
) -> str:
    """Build the evaluation prompt for execution readiness."""
    header = format_opportunity_header(opportunity)

    return f"""Evaluate this research for execution readiness (no final trade decision).

## Opportunity Details

{header}

## Full Research Context

{markdown_body}

## Your Task

1. Review the research above carefully
2. Identify whether flip risk is present based on the research
3. Write concise reasoning for Trader explaining why this should proceed or be rejected
4. Do not make a final BUY/NO decision (leave action unset)

## Important

- Be disciplined and conservative. When in doubt, downgrade risk
"""
