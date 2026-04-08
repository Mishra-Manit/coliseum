"""Web Researcher subagent for Scout — isolated search context per query."""

from dataclasses import replace

from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.profiles.openai import openai_model_profile

from coliseum.agents.agent_factory import _get_openai_provider, create_agent
from coliseum.config import get_settings
from coliseum.llm_providers import OpenAIModel

_WEB_RESEARCHER_PROMPT = """\
You are a web research specialist for a prediction market trading system.

Given a specific search query, run 1-2 focused web searches and return a concise synthesis.

## Research Process

1. Run 1-2 targeted searches. Stop IMMEDIATELY once you have enough facts to answer the query.
   Do not run additional searches for marginal coverage — speed matters.
2. Prioritize authoritative sources: official websites, news wires, government data, exchange data.
3. Extract specific facts — exact dates, exact thresholds, exact prices, official statements.

## Output Format

Return a structured plain-text synthesis covering:

**Status**: One of CONFIRMED / CANCELLED / POSTPONED / UNCERTAIN
**Key Facts**: 2-4 bullet points, each with a specific number or date and the source domain in brackets.
  Example: "BTC price was $87,234 at 4pm EST March 26 [coinmarketcap.com]"
**Disqualifiers**: Any active disputes, appeals, judicial reviews, cancellations, or postponements
  that would void or delay the contract. Write "None found" if none.
**Resolution Source**: The exact authoritative body or data feed that resolves this market.
**Sources**: List of https:// URLs used, one per line.

## Rules

- Never ask clarifying questions. Always search immediately and return findings.
- Never fabricate data or URLs. If searches return no useful results, say so explicitly.
- If the event status is uncertain after searching, report UNCERTAIN and explain why.
- Include specific numbers wherever possible — dates, prices, thresholds, percentages.
- Do not editorialize about probability or trading strategy. Report facts only.
"""

_web_researcher: Agent[None, str] | None = None


def get_web_researcher() -> Agent[None, str]:
    """Return the singleton web researcher agent, creating it on first call."""
    global _web_researcher
    if _web_researcher is None:
        settings = get_settings()
        if settings.llm.provider == "xai":
            _web_researcher = create_agent(
                prompt=_WEB_RESEARCHER_PROMPT,
                output_type=str,
                builtin_tools=[WebSearchTool()],
                prepend_mechanics=False,
            )
        else:
            provider = _get_openai_provider()
            model_name = OpenAIModel.GPT_5_2
            profile = replace(
                openai_model_profile(model_name),
                openai_supports_encrypted_reasoning_content=False,
            )
            model = OpenAIResponsesModel(model_name, provider=provider, profile=profile)
            model_settings = OpenAIResponsesModelSettings(
                timeout=120,
                openai_reasoning_effort='low',
            )
            _web_researcher = Agent(
                model=model,
                output_type=str,
                system_prompt=_WEB_RESEARCHER_PROMPT,
                model_settings=model_settings,
                builtin_tools=[WebSearchTool()],
            )
    return _web_researcher
