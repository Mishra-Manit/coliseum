"""
Event Selector

Uses LLM-based intelligent selection to pick the 5 most interesting events
for AI models to bet on from the available Kalshi markets.

Selection Criteria:
- Topical diversity across different domains
- Clear, objective resolution criteria
- Uncertain outcomes (prices near 50%)
- High market activity and liquidity
- Resolution within 24 hours

The selector uses Claude Sonnet 4.5 for intelligent event curation,
outputting structured data with selection reasoning and diversity scores.
"""

import json
import logging
from typing import Any

import logfire
from pydantic import BaseModel, Field

from pipeline.utils import create_agent

from .kalshi_client import KalshiEvent

# Configure module logger
logger = logging.getLogger(__name__)


class EventSelection(BaseModel):
    """
    Structured output from the LLM event selection.

    Contains the selected event tickers, reasoning for each selection,
    and metadata about the diversity of the selection.

    Attributes:
        selected_event_tickers: List of exactly 5 Kalshi event tickers
        selection_reasoning: Mapping of event ticker to selection rationale
        diversity_score: Score from 0-1 indicating topic diversity
        categories_covered: List of categories/domains represented
    """

    selected_event_tickers: list[str] = Field(
        description="Exactly 5 Kalshi event tickers selected for betting",
        min_length=5,
        max_length=5,
    )
    selection_reasoning: dict[str, str] = Field(
        description="Event ticker to selection reason mapping explaining why each event was chosen"
    )
    diversity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Topic diversity score (0 = all same category, 1 = maximally diverse)",
    )
    categories_covered: list[str] = Field(
        description="List of distinct categories/domains covered by the selection (e.g., Sports, Politics, Finance)",
    )


# System prompt for the event selection agent
SELECTION_SYSTEM_PROMPT = """You are an expert prediction market curator selecting the most interesting events for AI models to bet on in a competitive forecasting arena.

Your goal is to select exactly 5 events that will provide the most engaging and intellectually stimulating betting opportunities for AI forecasters.

## Selection Criteria (in order of importance)

### 1. TOPICAL DIVERSITY (Critical)
- Select events from DIFFERENT categories and domains
- Aim for a mix like: 1 Sports, 1 Politics, 1 Finance, 1 Tech/Science, 1 Entertainment/Other
- NEVER select multiple events from the same narrow topic (e.g., don't pick 5 NFL games)
- If most available events are sports, pick at most 2 sports events

### 2. OUTCOME UNCERTAINTY
- Prioritize events with prices near 50% (indicating uncertain outcomes)
- Markets with YES prices between 30-70 are ideal
- Avoid events where the outcome is nearly certain (>90% or <10%)

### 3. MARKET LIQUIDITY
- Prefer events with higher trading volume (more contracts traded)
- High volume indicates genuine market interest and reliable price signals

### 4. CLEAR RESOLUTION
- Select events with clear, objective resolution criteria
- The outcome should be verifiable within 24 hours
- Avoid events with ambiguous or subjective resolution

### 5. ANALYTICAL POTENTIAL
- Choose events where AI analysis can provide unique insights
- Events with available data, news, and research opportunities are preferred

## Output Requirements

For each selected event, provide:
1. The event ticker (exactly as shown in the data)
2. A brief explanation of why this event is interesting for AI forecasting
3. What category/domain it represents

Calculate a diversity score based on:
- 5 different categories = 1.0
- 4 different categories = 0.8
- 3 different categories = 0.6
- 2 different categories = 0.4
- 1 category (all same) = 0.2

Remember: The goal is to create an engaging, diverse competition that showcases AI forecasting across multiple domains."""


class EventSelector:
    """
    Selects the 5 most interesting events from available Kalshi markets using LLM.

    Uses Claude Sonnet 4.5 for intelligent event curation, prioritizing
    topical diversity, outcome uncertainty, and market liquidity.

    Usage:
        selector = EventSelector()
        selection = await selector.select_events(available_events)
    """

    def __init__(self, model: str = "anthropic:claude-sonnet-4-5"):
        """
        Initialize the event selector with a configured agent.

        Args:
            model: Model identifier for the selection agent.
                   Defaults to Claude Sonnet 4.5 for best reasoning.
        """
        self.model = model
        self.agent = create_agent(
            model=model,
            output_type=EventSelection,
            system_prompt=SELECTION_SYSTEM_PROMPT,
            temperature=0.2,  # Slightly creative for diverse selection
            retries=2,
            timeout=60.0,  # Allow time for thoughtful selection
        )
        logger.info(f"EventSelector initialized with model: {model}")

    async def select_events(
        self,
        available_events: list[KalshiEvent],
    ) -> EventSelection:
        """
        Select 5 events from the available Kalshi events.

        Args:
            available_events: List of KalshiEvent objects with market data

        Returns:
            EventSelection with 5 selected tickers, reasoning, and diversity score

        Raises:
            AgentExecutionError: If LLM selection fails after retries
            ValueError: If fewer than 5 events are available
        """
        if len(available_events) < 5:
            raise ValueError(
                f"Need at least 5 events to select from, got {len(available_events)}"
            )

        with logfire.span("ingestion.event_selection"):
            logfire.info(
                "Starting event selection",
                available_events=len(available_events),
                model=self.model,
            )

            # Build the prompt with event data
            prompt = self._build_selection_prompt(available_events)

            # Run the agent to select events
            result = await self.agent.run(prompt)
            selection: EventSelection = result.data

            # Validate that all selected tickers exist in available events
            available_tickers = {event.event_ticker for event in available_events}
            invalid_tickers = [
                t for t in selection.selected_event_tickers if t not in available_tickers
            ]

            if invalid_tickers:
                logfire.warn(
                    "LLM selected invalid tickers",
                    invalid=invalid_tickers,
                    valid_count=len(selection.selected_event_tickers) - len(invalid_tickers),
                )

            logfire.info(
                "Events selected successfully",
                selected_count=len(selection.selected_event_tickers),
                diversity_score=selection.diversity_score,
                categories=selection.categories_covered,
                selected_tickers=selection.selected_event_tickers,
            )

            return selection

    def _build_selection_prompt(self, events: list[KalshiEvent]) -> str:
        """
        Build the prompt for LLM event selection.

        Formats event data in a clear, structured way for the LLM to analyze.

        Args:
            events: List of KalshiEvent objects

        Returns:
            Formatted prompt string with all event data
        """
        prompt_parts = [
            "# Event Selection Task",
            "",
            "Select exactly 5 events from the following list that would be most interesting for AI models to bet on.",
            "Prioritize DIVERSITY across different topics/categories.",
            "",
            f"## Available Events ({len(events)} total)",
            "",
        ]

        # Group events by inferred category for better LLM context
        categorized = self._categorize_events(events)

        for category, category_events in categorized.items():
            prompt_parts.append(f"### {category} ({len(category_events)} events)")
            prompt_parts.append("")

            for event in category_events:
                # Build event summary
                markets_info = self._format_markets_summary(event.markets)

                prompt_parts.append(f"**Event Ticker**: `{event.event_ticker}`")
                prompt_parts.append(f"- Title: {event.title}")
                prompt_parts.append(f"- Total Volume: {event.formatted_total_volume} contracts")
                prompt_parts.append(f"- Markets: {event.market_count}")
                prompt_parts.append(f"- Closes: {event.close_time}")
                prompt_parts.append(f"- Uncertainty: {event.average_uncertainty:.1%}")
                prompt_parts.append(f"- Market Details: {markets_info}")
                prompt_parts.append("")

        prompt_parts.extend([
            "---",
            "",
            "## Your Task",
            "",
            "1. Select exactly 5 events with maximum topical diversity",
            "2. Provide reasoning for each selection",
            "3. List the categories covered",
            "4. Calculate the diversity score",
            "",
            "Return your selection as structured data.",
        ])

        return "\n".join(prompt_parts)

    def _categorize_events(
        self,
        events: list[KalshiEvent],
    ) -> dict[str, list[KalshiEvent]]:
        """
        Group events by inferred category for prompt organization.

        Uses event ticker patterns and titles to infer categories
        since Kalshi's category field is often empty.

        Args:
            events: List of events to categorize

        Returns:
            Dictionary mapping category name to list of events
        """
        categories: dict[str, list[KalshiEvent]] = {}

        for event in events:
            category = self._infer_category(event)
            if category not in categories:
                categories[category] = []
            categories[category].append(event)

        return categories

    def _infer_category(self, event: KalshiEvent) -> str:
        """
        Infer event category from ticker and title patterns.

        Args:
            event: KalshiEvent to categorize

        Returns:
            Inferred category string
        """
        ticker = event.event_ticker.upper()
        title = event.title.lower()

        # Sports patterns
        if any(sport in ticker for sport in ["NFL", "NBA", "MLB", "NHL", "MLS", "UFC", "GAME"]):
            return "Sports"
        if any(sport in title for sport in ["game", "match", "win", "score", "player", "team"]):
            return "Sports"

        # Politics patterns
        if any(pol in ticker for pol in ["PRES", "ELECT", "VOTE", "GOV", "SEN", "CONG"]):
            return "Politics"
        if any(pol in title for pol in ["president", "election", "vote", "congress", "senate"]):
            return "Politics"

        # Finance/Economics patterns
        if any(fin in ticker for fin in ["FED", "RATE", "GDP", "CPI", "INX", "SPX", "BTC", "CRYPTO"]):
            return "Finance"
        if any(fin in title for fin in ["rate", "fed", "stock", "bitcoin", "crypto", "price"]):
            return "Finance"

        # Technology patterns
        if any(tech in ticker for tech in ["AI", "TECH", "APPLE", "GOOGLE", "META"]):
            return "Technology"
        if any(tech in title for tech in ["ai", "tech", "apple", "google", "launch", "release"]):
            return "Technology"

        # Entertainment patterns
        if any(ent in ticker for ent in ["OSCAR", "EMMY", "GRAMMY", "MOVIE", "TV"]):
            return "Entertainment"
        if any(ent in title for ent in ["oscar", "emmy", "grammy", "award", "movie", "show"]):
            return "Entertainment"

        # Weather patterns
        if any(weather in ticker for weather in ["WEATHER", "TEMP", "RAIN", "SNOW"]):
            return "Weather"

        # Use Kalshi's category if available
        if event.category:
            return event.category.title()

        return "Other"

    def _format_markets_summary(self, markets: list[Any]) -> str:
        """
        Create a brief summary of markets in an event.

        Args:
            markets: List of KalshiMarket objects

        Returns:
            Brief formatted string describing the markets
        """
        if not markets:
            return "No markets"

        if len(markets) == 1:
            m = markets[0]
            return f"YES: {m.yes_bid}¢, Volume: {m.formatted_volume}"

        # Summarize multiple markets
        total_vol = sum(m.volume for m in markets)
        avg_yes = sum(m.yes_bid for m in markets) / len(markets)

        vol_str = f"{total_vol / 1000:.1f}K" if total_vol >= 1000 else str(total_vol)
        return f"{len(markets)} outcomes, Avg YES: {avg_yes:.0f}¢, Total Vol: {vol_str}"
