"""Researcher Agent: Deep research and synthesis without trading decisions."""

import logging
import time
from datetime import datetime, timezone
from typing import Literal

from pydantic_ai import Agent, WebSearchTool

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.analyst.models import AnalystDependencies, ResearcherOutput
from coliseum.agents.analyst.prompts import (
    RESEARCHER_SURE_THING_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
)
from coliseum.agents.analyst.shared import (
    format_opportunity_header,
    load_and_validate_opportunity,
)
from coliseum.config import Settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import OpportunitySignal, append_to_opportunity

logger = logging.getLogger(__name__)


def _create_agent(strategy: str = "edge") -> Agent[AnalystDependencies, ResearcherOutput]:
    prompt = RESEARCHER_SURE_THING_PROMPT if strategy == "sure_thing" else RESEARCHER_SYSTEM_PROMPT
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=ResearcherOutput,
        deps_type=AnalystDependencies,
        system_prompt=prompt,
        builtin_tools=[WebSearchTool()],
    )


_edge_factory = AgentFactory(create_fn=lambda: _create_agent("edge"))
_sure_thing_factory = AgentFactory(create_fn=lambda: _create_agent("sure_thing"))


def get_agent(strategy: str = "edge") -> Agent[AnalystDependencies, ResearcherOutput]:
    """Get the singleton Researcher agent instance for the given strategy."""
    if strategy == "sure_thing":
        return _sure_thing_factory.get_agent()
    return _edge_factory.get_agent()


async def run_researcher(
    opportunity_id: str,
    settings: Settings,
    strategy: Literal["edge", "sure_thing"] | None = None,
) -> ResearcherOutput:
    """Run Researcher agent - appends research to opportunity file."""
    start_time = time.time()
    logger.info(f"Starting Researcher for opportunity: {opportunity_id}")

    opp_file, opportunity, resolved_strategy = load_and_validate_opportunity(
        opportunity_id, strategy
    )
    logger.info(
        f"Researcher strategy resolved: {resolved_strategy} (file={opportunity.strategy})"
    )

    deps = AnalystDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    prompt = _build_research_prompt(opportunity, settings)

    agent = get_agent(resolved_strategy)
    result = await agent.run(prompt, deps=deps)
    output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    research_section = f"""---

## Research Synthesis

{output.synthesis}"""

    frontmatter_updates = {
        "research_completed_at": completed_at.isoformat(),
        "research_duration_seconds": int(duration),
    }

    append_to_opportunity(
        market_ticker=opportunity.market_ticker,
        frontmatter_updates=frontmatter_updates,
        body_section=research_section,
        section_header="## Research Synthesis",
    )

    logger.info(
        f"Researcher completed in {duration:.1f}s - "
        f"Appended to {opportunity.market_ticker}"
    )

    return output


def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
    """Build the research prompt for the agent."""
    header = format_opportunity_header(opportunity)

    return f"""Research this prediction market opportunity and synthesize your findings.

## Opportunity Details

{header}

**Scout's Rationale**: {opportunity.rationale}

## Your Task

1. Formulate 2-4 very specific research questions about this event
2. Use web search for each question to gather grounded information
3. Synthesize findings into a coherent analysis with embedded sources

## Research Standards

- **Objectivity**: Consider both bullish and bearish evidence
- **Grounding**: Only cite facts from web search results (no hallucination)
- **Base rates**: Start with historical precedents, then adjust for specifics

## Important

You are ONLY responsible for research. Do NOT:
- Estimate probability of YES outcome
- Calculate edge or expected value
- Make trade recommendations (BUY/SELL/ABSTAIN)

The Recommender agent will handle the trading decision based on your research.
"""
