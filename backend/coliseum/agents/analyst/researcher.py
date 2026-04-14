"""Researcher Agent: Deep research and synthesis without trading decisions."""

import logging
import time
from datetime import datetime, timezone

import logfire
from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.markets_context import get_market_type_context
from coliseum.agents.analyst.models import AnalystDependencies, ResearcherOutput
from coliseum.agents.analyst.prompts import RESEARCHER_PROMPT
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_opportunity,
)
from coliseum.agents.analyst.web_researcher import get_web_researcher
from coliseum.agents.shared_tools import strip_cite_tokens
from coliseum.config import Settings
from coliseum.llm_providers import GrokModel
from coliseum.memory.context import build_analyst_context
from coliseum.services.supabase.repositories.opportunities import update_opportunity_research
from coliseum.domain.opportunity import OpportunitySignal

logger = logging.getLogger(__name__)


def _create_agent() -> Agent[AnalystDependencies, ResearcherOutput]:
    return create_agent(
        prompt=RESEARCHER_PROMPT,
        output_type=ResearcherOutput,
        deps_type=AnalystDependencies,
        reasoning_effort="medium",
        xai_model=GrokModel.GROK_4_20_NON_REASONING,
    )


def _register_research_tool(agent: Agent[AnalystDependencies, ResearcherOutput]) -> None:
    @agent.tool
    async def research_topic(ctx: RunContext[AnalystDependencies], query: str) -> str:
        """Search the web for a specific query and return a research synthesis."""
        researcher = get_web_researcher()
        result = await researcher.run(query, usage=ctx.usage)
        return result.output


_agent_factory = AgentFactory(create_fn=_create_agent, register_tools_fn=_register_research_tool)


def get_agent() -> Agent[AnalystDependencies, ResearcherOutput]:
    """Get the singleton Researcher agent instance."""
    return _agent_factory.get_agent()


async def run_researcher(
    opportunity_id: str,
    settings: Settings,
) -> ResearcherOutput:
    """Run Researcher agent - writes research synthesis to DB."""
    start_time = time.time()
    opportunity = await load_opportunity(opportunity_id)

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
    )
    prompt = await _build_research_prompt(opportunity, settings)

    agent = get_agent()
    result = await agent.run(prompt, deps=deps)
    output = result.output
    output = ResearcherOutput(synthesis=strip_cite_tokens(output.synthesis))

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    try:
        await update_opportunity_research(
            opportunity_id=opportunity_id,
            synthesis=output.synthesis,
            completed_at=completed_at,
            duration_seconds=int(duration),
        )
    except Exception as e:
        logfire.error("DB write failed for researcher", opportunity_id=opportunity_id, error=str(e))

    logfire.info(
        "Researcher complete",
        ticker=opportunity.market_ticker,
        duration_seconds=round(duration, 1),
    )

    return output


async def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
    """Build the research prompt for the agent."""
    header = format_opportunity_header(opportunity)
    memory_context = await build_analyst_context()
    market_type_context = await get_market_type_context(opportunity)

    return f"""Assess whether this pre-resolution prediction market is likely to hold at 92-96% YES.
{memory_context}
## Opportunity Details

{header}

**Scout's Rationale**: {opportunity.rationale}

## Market Type

{market_type_context}

## Research Task

Call research_topic 3 times using the query structure in your instructions. Use the market-type
context above to skip calls you can already answer. Report what each call returned — including
null results.
"""
