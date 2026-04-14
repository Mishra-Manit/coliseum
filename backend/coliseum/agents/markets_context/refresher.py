"""Grok-powered refresher agent for market category context.

Two-stage pipeline per category:
  1. Web researcher (str output + WebSearchTool) — gathers raw research
  2. Structurer (CategoryRefreshOutput, no tools) — parses into structured data

This split is required because xAI's gRPC SDK hangs when WebSearchTool is
combined with structured Pydantic output in a single agent call.
"""

from __future__ import annotations

import logging
import time

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, WebSearchTool

from coliseum.agents.agent_factory import create_agent
from coliseum.agents.markets_context.seed_data import (
    FALLBACK,
    MARKET_TYPES,
    MarketTypeConfig,
)
from coliseum.llm_providers import GrokModel
from coliseum.services.supabase.repositories.market_context import upsert_category_context

logger = logging.getLogger(__name__)


class CategoryRefreshOutput(BaseModel):
    """Structured output from the structurer agent."""

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


# Stage 1: Web research agent (str output so WebSearchTool works on xAI gRPC)
_RESEARCHER_PROMPT = """\
You are a Kalshi prediction market resolution rules researcher. Your job is to gather \
comprehensive raw research for a single market category.

## Research Process

Run exactly 3 web searches, one per topic:

1. **Official Resolution Rules**: Search for Kalshi's exact resolution criteria for this \
market type. Find the official rules page, FAQ entries, help articles. What data source is \
used? What exact timestamp or measurement is the trigger?

2. **Past Disputes & Unexpected Resolutions**: Search X (Twitter), Reddit (r/kalshi, \
r/predictionmarkets), and Kalshi community forums for disputes, complaints, or unexpected \
resolutions on this market type.

3. **Edge Cases & Ambiguities**: Search for structural ambiguities. For sports: overtime, \
forfeits, postponements. For economic data: revisions, delayed releases. For mentions: \
exact vs partial word matching, transcript source disputes.

## Output Rules

- Be specific with dates, numbers, and exact rules.
- Include all URLs you referenced.
- If you find nothing for disputes or edge cases, say so explicitly.
- Never include internal citation markers (e.g. citeturn10view0).
"""

# Stage 2: Structurer agent (no tools, structured output)
_STRUCTURER_PROMPT = """\
You are a data structuring assistant. You receive raw research about a Kalshi prediction \
market category and must extract it into a structured format.

## Rules

- resolution_rules: 300-500 words covering exact resolution mechanics, data source, timing.
- known_disputes: Past disputes with dates and specifics. Empty string if none found.
- edge_cases: Structural ambiguities. Empty string if none found.
- risk_questions: 5-8 specific questions a researcher should answer before trading. Each \
  should target a concrete data point answerable with a single web search.
- sources: All URLs mentioned in the research.
- Do not fabricate information not present in the raw research.
"""

_researcher: Agent[None, str] | None = None
_structurer: Agent[None, CategoryRefreshOutput] | None = None


def _get_researcher() -> Agent[None, str]:
    """Return the singleton web research agent."""
    global _researcher
    if _researcher is None:
        _researcher = create_agent(
            prompt=_RESEARCHER_PROMPT,
            output_type=str,
            builtin_tools=[WebSearchTool()],
            prepend_mechanics=False,
            xai_model=GrokModel.GROK_4_20_NON_REASONING,
        )
    return _researcher


def _get_structurer() -> Agent[None, CategoryRefreshOutput]:
    """Return the singleton structurer agent."""
    global _structurer
    if _structurer is None:
        _structurer = create_agent(
            prompt=_STRUCTURER_PROMPT,
            output_type=CategoryRefreshOutput,
            prepend_mechanics=False,
            xai_model=GrokModel.GROK_4_20_NON_REASONING,
        )
    return _structurer


def _build_research_prompt(category_key: str, config: MarketTypeConfig) -> str:
    """Build the user prompt for the web research stage."""
    existing_questions = "\n".join(f"- {q}" for q in config.risk_questions)
    return (
        f"Research the Kalshi prediction market category: **{config.label}**\n\n"
        f"Category key: {category_key}\n"
        f"Resolution template: {config.resolution_desc}\n\n"
        f"Current risk questions (use as starting context, improve on these):\n"
        f"{existing_questions}\n\n"
        f"Search the web 3 times as instructed in your system prompt."
    )


async def refresh_category(category_key: str) -> None:
    """Research a category via web search, structure the result, and persist to DB."""
    config = MARKET_TYPES.get(category_key, FALLBACK)

    start = time.time()
    with logfire.span("market context refresh", category_key=category_key, label=config.label):
        # Stage 1: web research -> raw text
        research_prompt = _build_research_prompt(category_key, config)
        raw_result = await _get_researcher().run(research_prompt)
        raw_research = raw_result.output

        # Stage 2: structure the raw research
        structure_result = await _get_structurer().run(
            f"Structure this raw research for category '{config.label}':\n\n{raw_research}"
        )
        output = structure_result.output
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
