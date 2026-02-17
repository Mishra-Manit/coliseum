"""Researcher Agent: Deep research and synthesis without trading decisions."""

import logging
import time
from datetime import datetime, timezone
from pydantic_ai import Agent, RunContext, WebSearchTool

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.analyst.researcher.models import (
    ResearcherDependencies,
    ResearcherOutput,
)
from coliseum.agents.analyst.researcher.prompts import RESEARCHER_SYSTEM_PROMPT, RESEARCHER_SURE_THING_PROMPT
from coliseum.agents.shared_tools import register_load_opportunity
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    find_opportunity_file_by_id,
    load_opportunity_from_file,
    update_opportunity_status,
)

logger = logging.getLogger(__name__)


def _create_agent(strategy: str = "edge") -> Agent[ResearcherDependencies, ResearcherOutput]:
    prompt = RESEARCHER_SURE_THING_PROMPT if strategy == "sure_thing" else RESEARCHER_SYSTEM_PROMPT
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=ResearcherOutput,
        deps_type=ResearcherDependencies,
        system_prompt=prompt,
        builtin_tools=[WebSearchTool()],
    )


def _register_tools(agent: Agent[ResearcherDependencies, ResearcherOutput]) -> None:
    register_load_opportunity(agent)


_edge_factory = AgentFactory(
    create_fn=lambda: _create_agent("edge"),
    register_tools_fn=_register_tools,
)

_sure_thing_factory = AgentFactory(
    create_fn=lambda: _create_agent("sure_thing"),
    register_tools_fn=_register_tools,
)


def get_agent(strategy: str = "edge") -> Agent[ResearcherDependencies, ResearcherOutput]:
    """Get the singleton Researcher agent instance for the given strategy."""
    if strategy == "sure_thing":
        return _sure_thing_factory.get_agent()
    return _edge_factory.get_agent()


async def run_researcher(
    opportunity_id: str,
    settings: Settings,
    dry_run: bool = False,
) -> ResearcherOutput:
    """Run Researcher agent - appends research to opportunity file."""
    start_time = time.time()
    logger.info(f"Starting Researcher for opportunity: {opportunity_id}")

    # Find opportunity file
    opp_file = find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    opportunity = load_opportunity_from_file(opp_file)
    strategy = opportunity.strategy

    # Update status to "researching"
    if not dry_run:
        update_opportunity_status(opportunity.market_ticker, "researching")

    # Run research
    deps = ResearcherDependencies(
        opportunity_id=opportunity_id,
        config=settings.analyst,
    )
    prompt = _build_research_prompt(opportunity, settings)

    agent = get_agent(strategy)
    result = await agent.run(prompt, deps=deps)
    output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    # Prepare research section for append (synthesis now includes embedded sources)
    research_section = f"""---

## Research Synthesis

{output.synthesis}"""

    # Prepare frontmatter updates
    frontmatter_updates = {
        "research_completed_at": completed_at.isoformat(),
        "research_duration_seconds": int(duration),
    }

    # Append to opportunity file
    if not dry_run:
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

    # Return output (sources are now embedded in synthesis)
    return output


def _build_research_prompt(opportunity: OpportunitySignal, settings: Settings) -> str:
    """Build the research prompt for the agent."""
    subtitle_info = (
        f"**Specific Outcome**: {opportunity.subtitle}\n\n"
        if opportunity.subtitle
        else ""
    )

    prompt = f"""Research this prediction market opportunity and synthesize your findings.

## Opportunity Details

**Market**: {opportunity.title}
{subtitle_info}**Current YES Price**: {opportunity.yes_price:.2f} ({opportunity.yes_price * 100:.1f}¢)
**Current NO Price**: {opportunity.no_price:.2f} ({opportunity.no_price * 100:.1f}¢)
**Market Closes**: {opportunity.close_time.isoformat()}

**Scout's Rationale**: {opportunity.rationale}

## Your Task

1. Use `load_opportunity` to get full opportunity data
2. Formulate 2-4 specific research questions about this event
3. Use web search for each question to gather grounded information
4. Synthesize findings into a coherent analysis with embedded sources

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

    return prompt
