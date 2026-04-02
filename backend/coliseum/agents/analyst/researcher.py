"""Researcher Agent: Deep research and synthesis without trading decisions."""

import logging
import time
from datetime import datetime, timezone

import logfire
from pydantic_ai import Agent, WebSearchTool

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.analyst.market_type_context import get_market_type_context
from coliseum.agents.analyst.models import AnalystDependencies, ResearcherOutput
from coliseum.agents.analyst.prompts import RESEARCHER_PROMPT
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_opportunity,
)
from coliseum.agents.shared_tools import _strip_cite_tokens
from coliseum.config import Settings
from coliseum.memory.context import build_analyst_context
from coliseum.services.supabase.repositories.opportunities import update_opportunity_research
from coliseum.storage.files import OpportunitySignal, append_to_opportunity

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[AnalystDependencies, ResearcherOutput]:
    return create_agent(
        prompt=RESEARCHER_PROMPT,
        output_type=ResearcherOutput,
        deps_type=AnalystDependencies,
        reasoning_effort="medium",
        builtin_tools=[WebSearchTool()],
    )


_agent_factory = AgentFactory(create_fn=_create_agent)


def get_agent() -> Agent[AnalystDependencies, ResearcherOutput]:
    """Get the singleton Researcher agent instance."""
    return _agent_factory.get_agent()


async def run_researcher(
    opportunity_id: str,
    settings: Settings,
) -> ResearcherOutput:
    """Run Researcher agent - appends research to opportunity file."""
    start_time = time.time()
    opp_file, opportunity = load_opportunity(opportunity_id, paper=settings.trading.paper_mode)

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
    )
    prompt = _build_research_prompt(opportunity, settings)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output
    output = ResearcherOutput(synthesis=_strip_cite_tokens(output.synthesis))

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    research_section = f"""---

## Research Synthesis

{output.synthesis}"""

    frontmatter_updates = {
        "research_completed_at": completed_at.isoformat(),
        "research_duration_seconds": int(duration),
    }

    try:
        await update_opportunity_research(
            opportunity_id=opportunity_id,
            synthesis=output.synthesis,
            completed_at=completed_at,
            duration_seconds=int(duration),
        )
    except Exception as e:
        logfire.error("DB write failed for researcher", opportunity_id=opportunity_id, error=str(e))

    append_to_opportunity(
        market_ticker=opportunity.market_ticker,
        frontmatter_updates=frontmatter_updates,
        body_section=research_section,
        section_header="## Research Synthesis",
        paper=settings.trading.paper_mode,
    )

    logfire.info(
        "Researcher complete",
        ticker=opportunity.market_ticker,
        duration_seconds=round(duration, 1),
    )

    return output


def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
    """Build the research prompt for the agent."""
    header = format_opportunity_header(opportunity)
    memory_context = build_analyst_context()
    market_type_context = get_market_type_context(opportunity)

    return f"""Assess whether this pre-resolution prediction market is likely to hold at 92-96% YES.
{memory_context}
## Opportunity Details

{header}

**Scout's Rationale**: {opportunity.rationale}

## Market Type

{market_type_context}

## Research Task

Follow the 3-search workflow in your instructions. Use the market-type context above to skip
searches you can already answer. Report what each search returned — including null results.
"""
