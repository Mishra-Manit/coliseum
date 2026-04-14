"""Grok-powered refresher agent for market category context.

For each category, runs web searches via Grok non-reasoning + WebSearchTool
and produces a structured synthesis of resolution rules, disputes, and edge cases.
"""

from __future__ import annotations

import logging
import time

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, WebSearchTool

from coliseum.agents.agent_factory import create_agent
from coliseum.agents.analyst.markets_context.market_type_context import (
    MARKET_TYPES,
    MarketTypeConfig,
    _FALLBACK,
)
from coliseum.llm_providers import GrokModel
from coliseum.services.supabase.repositories.market_context import upsert_category_context

logger = logging.getLogger(__name__)



class CategoryRefreshOutput(BaseModel):
    """Structured output from the refresher agent."""

    resolution_rules: str = Field(
        description=(
            "Comprehensive resolution mechanics: data source, timing, exact trigger, "
            "measurement details. 300-500 words."
        ),
    )
    known_disputes: str = Field(
        default="",
        description=(
            "Past disputes, unexpected resolutions, community complaints with dates "
            "and specifics. Empty string if none found."
        ),
    )
    edge_cases: str = Field(
        default="",
        description=(
            "Structural ambiguities, overtime rules, delayed releases, methodology "
            "changes. Empty string if none found."
        ),
    )
    risk_questions: list[str] = Field(
        description="5-8 specific risk questions a researcher should answer before trading this market type.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="URLs cited during research.",
    )


_REFRESHER_PROMPT = """\
You are a Kalshi prediction market resolution rules researcher. Your job is to produce a \
comprehensive reference document for a single market category that a trading agent will use \
to assess flip risk on 92-96 cent YES contracts.

## Research Process

Run exactly 3 web searches, one per topic:

1. **Official Resolution Rules**: Search for Kalshi's exact resolution criteria for this \
market type. Find the official rules page, FAQ entries, help articles. What data source is \
used? What exact timestamp or measurement is the trigger? What does Kalshi explicitly include \
or exclude?

2. **Past Disputes & Unexpected Resolutions**: Search X (Twitter), Reddit (r/kalshi, \
r/predictionmarkets), and Kalshi community forums for disputes, complaints, or unexpected \
resolutions on this market type. Has Kalshi ever voided a market in this category? Has a \
resolution source been delayed or changed? Include specific examples with dates if found.

3. **Edge Cases & Ambiguities**: Search for structural ambiguities — situations where the \
resolution rules are unclear or have been interpreted differently. For sports: overtime, \
forfeits, postponements. For economic data: revisions, delayed releases, methodology changes. \
For mentions: exact vs partial word matching, transcript source disputes.

## Output Rules

- Be specific. "BLS releases CPI-U on the second Tuesday at 8:30 AM ET" is useful. \
  "CPI data comes from the government" is not.
- Include dates and examples from past incidents wherever possible.
- If you find nothing for known_disputes or edge_cases, return an empty string. \
  Do not fabricate incidents.
- risk_questions must be specific to THIS market category, not generic. Each question should \
  target a concrete data point or risk factor that a researcher can answer with a single web search.
- Never include internal citation markers (e.g. citeturn10view0) in your output.
- Include all URLs you referenced in the sources list.
"""

def _create_refresher_agent() -> Agent[None, CategoryRefreshOutput]:
    """Create a fresh refresher agent instance."""
    return create_agent(
        prompt=_REFRESHER_PROMPT,
        output_type=CategoryRefreshOutput,
        builtin_tools=[WebSearchTool()],
        prepend_mechanics=False,
        xai_model=GrokModel.GROK_4_20_NON_REASONING,
    )


def _build_refresh_prompt(category_key: str, config: MarketTypeConfig) -> str:
    """Build the user prompt for a single category refresh."""
    existing_questions = "\n".join(f"- {q}" for q in config.risk_questions)
    return (
        f"Research the Kalshi prediction market category: **{config.label}**\n\n"
        f"Category key: {category_key}\n"
        f"Resolution template: {config.resolution_desc}\n\n"
        f"Current risk questions (use as starting context, improve on these):\n"
        f"{existing_questions}\n\n"
        f"Produce a comprehensive reference document for this category. "
        f"Search the web 3 times as instructed in your system prompt."
    )


async def refresh_category(category_key: str) -> None:
    """Run the Grok refresher agent for a single category and persist the result."""
    config = MARKET_TYPES.get(category_key, _FALLBACK)
    prompt = _build_refresh_prompt(category_key, config)

    start = time.time()
    with logfire.span("market context refresh", category_key=category_key, label=config.label):
        agent = _create_refresher_agent()
        result = await agent.run(prompt)
        output = result.output
        duration = int(time.time() - start)

        await upsert_category_context(
            category_key=category_key,
            label=config.label,
            resolution_desc_template=config.resolution_desc,
            uses_slug=config.uses_slug,
            resolution_rules=output.resolution_rules,
            known_disputes=output.known_disputes,
            edge_cases=output.edge_cases,
            risk_questions=output.risk_questions,
            sources=output.sources,
            refresh_duration_seconds=duration,
        )

        logger.info("Refreshed %s (%s) in %ds", category_key, config.label, duration)


async def refresh_all_categories() -> int:
    """Refresh every category in MARKET_TYPES sequentially. Returns success count."""
    keys = list(MARKET_TYPES.keys())
    total = len(keys)
    refreshed = 0

    with logfire.span("market context full refresh", total_categories=total):
        for key in keys:
            try:
                await refresh_category(key)
                refreshed += 1
            except Exception as e:
                logger.error("Skipping %s after refresh failure: %s", key, e)

        logger.info("Market context full refresh complete: %d/%d", refreshed, total)

    return refreshed
