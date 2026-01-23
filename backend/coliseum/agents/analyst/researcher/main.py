"""Researcher Agent: Deep research and synthesis without trading decisions."""

import logging
import os
import time
from datetime import datetime, timezone
from pydantic_ai import Agent, RunContext

from coliseum.agents.analyst.researcher.models import (
    ResearcherDependencies,
    ResearcherOutput,
)
from coliseum.agents.analyst.researcher.prompts import RESEARCHER_SYSTEM_PROMPT
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import FireworksModel, get_model_string
from coliseum.services.exa.client import ExaClient
from coliseum.storage.files import (
    OpportunitySignal,
    append_to_opportunity,
    find_opportunity_file_by_id,
    load_opportunity_from_file,
    update_opportunity_status,
)
from coliseum.storage.state import update_market_status

logger = logging.getLogger(__name__)

_agent: Agent[ResearcherDependencies, ResearcherOutput] | None = None


def get_agent() -> Agent[ResearcherDependencies, ResearcherOutput]:
    global _agent
    if _agent is None:
        settings = get_settings()
        if settings.fireworks_api_key:
            os.environ["FIREWORKS_API_KEY"] = settings.fireworks_api_key
        _agent = _create_agent()
    return _agent


def _create_agent() -> Agent[ResearcherDependencies, ResearcherOutput]:
    agent = Agent(
        model=get_model_string(FireworksModel.DEEPSEEK_V3_2),
        output_type=ResearcherOutput,
        deps_type=ResearcherDependencies,
        system_prompt=RESEARCHER_SYSTEM_PROMPT,
    )
    _register_tools(agent)
    return agent


def _register_tools(agent: Agent[ResearcherDependencies, ResearcherOutput]) -> None:
    @agent.tool
    async def fetch_opportunity_details(
        ctx: RunContext[ResearcherDependencies],
    ) -> dict:
        """Fetch opportunity details from file (market info, prices, close time, Scout's rationale)."""
        opportunity_id = ctx.deps.opportunity_id
        file_path = find_opportunity_file_by_id(opportunity_id)
        if not file_path:
            raise FileNotFoundError(
                f"Opportunity file not found for ID: {opportunity_id}"
            )

        opportunity = load_opportunity_from_file(file_path)
        return {
            "id": opportunity.id,
            "event_ticker": opportunity.event_ticker,
            "market_ticker": opportunity.market_ticker,
            "title": opportunity.title,
            "subtitle": opportunity.subtitle,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "close_time": opportunity.close_time.isoformat(),
            "rationale": opportunity.rationale,
            "status": opportunity.status,
            "discovered_at": opportunity.discovered_at.isoformat(),
        }

    @agent.tool
    async def exa_answer(
        ctx: RunContext[ResearcherDependencies],
        question: str,
    ) -> dict:
        """Ask research question using Exa AI. Returns answer with citations from credible sources."""
        exa_client = ctx.deps.exa_client

        logger.info(f"Exa research query: {question}")

        try:
            response = await exa_client.answer(
                question=question,
                include_text=True,
            )

            citations = [
                {
                    "url": citation.url,
                    "title": citation.title,
                    "text": citation.text[:500] if citation.text else "",
                }
                for citation in response.citations
            ]

            return {
                "answer": response.answer,
                "citations": citations,
                "query": response.query,
            }

        except Exception as e:
            logger.error(f"Exa API error: {e}")
            raise

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

    # Update status to "researching"
    if not dry_run:
        update_opportunity_status(opportunity.market_ticker, "researching")
        update_market_status(opportunity.market_ticker, "researching")

    # Run research
    async with ExaClient(api_key=settings.exa_api_key) as exa_client:
        deps = ResearcherDependencies(
            exa_client=exa_client,
            opportunity_id=opportunity_id,
            config=settings.analyst,
        )
        prompt = _build_research_prompt(opportunity, settings)

        agent = get_agent()
        result = await agent.run(prompt, deps=deps)
        output = result.output

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc)

    # Prepare research section for append
    sources_md = "\n".join(
        f"{i+1}. [{src}]({src})" for i, src in enumerate(output.sources)
    )

    research_section = f"""---

## Research Synthesis

{output.synthesis}

### Sources

{sources_md}"""

    # Prepare frontmatter updates
    frontmatter_updates = {
        "research_completed_at": completed_at.isoformat(),
        "research_sources_count": len(output.sources),
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

    # Return simplified output (no analysis_id)
    return ResearcherOutput(
        synthesis=output.synthesis,
        sources=output.sources,
        summary=output.summary,
        sources_count=len(output.sources),
    )


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

1. Use `fetch_opportunity_details` to get full opportunity data
2. Formulate 2-4 specific research questions about this event
3. Use `exa_answer` tool for each question to gather grounded information
4. Synthesize findings into a coherent analysis draft (minimum {settings.analyst.required_sources} sources)

## Research Standards

- **Objectivity**: Consider both bullish and bearish evidence
- **Grounding**: Only cite facts from Exa AI responses (no hallucination)
- **Base rates**: Start with historical precedents, then adjust for specifics

## Important

You are ONLY responsible for research. Do NOT:
- Estimate probability of YES outcome
- Calculate edge or expected value
- Make trade recommendations (BUY/SELL/ABSTAIN)

The Recommender agent will handle the trading decision based on your research.
"""

    return prompt
