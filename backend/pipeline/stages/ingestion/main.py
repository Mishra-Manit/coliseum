"""
IngestionStage - Pipeline Stage 1

Main stage implementation for event ingestion, the first step in the
daily prediction market competition pipeline.

Process:
1. API Fetch - Query Kalshi for markets closing within 24 hours
2. Volume Filtering - Keep only markets with 20,000+ contracts traded
3. Event Grouping - Group markets by parent event ticker
4. LLM Selection - Use Claude to select 5 most interesting events
5. Output Assembly - Package selected events with full market data

Outputs:
- selected_events: List[KalshiEvent] (exactly 5 events)
- selection_reasoning: Dict mapping event ticker to selection rationale
- metadata: Dict with events_scanned, markets_scanned, categories_covered

The output preserves all Kalshi market data for downstream pipeline stages.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import logfire

from .kalshi_client import (
    KalshiClient,
    KalshiConfig,
    KalshiEvent,
    KalshiMarket,
    IngestionOutput,
    group_markets_by_event,
)
from .selector import EventSelector, EventSelection

# Configure module logger
logger = logging.getLogger(__name__)


class IngestionStageError(Exception):
    """Raised when the ingestion stage encounters an unrecoverable error."""

    pass


class IngestionStage:
    """
    Stage 1: Event Ingestion

    Fetches prediction markets from Kalshi, filters by volume and close time,
    groups them into events, and uses LLM to select the 5 most interesting
    events for the day's AI forecasting competition.

    The stage is designed to be run once daily as part of the pipeline,
    outputting structured event data that flows to subsequent stages.

    Attributes:
        min_volume: Minimum contract volume threshold (default: 20,000)
        selector_model: LLM model for event selection

    Usage:
        stage = IngestionStage()
        output = await stage.execute()

        # Access selected events
        for event in output.selected_events:
            print(f"{event.event_ticker}: {event.title}")
            for market in event.markets:
                print(f"  - {market.ticker}: YES {market.yes_bid}¢")
    """

    def __init__(
        self,
        min_volume: int = KalshiConfig.DEFAULT_MIN_VOLUME,
        selector_model: str = "anthropic:claude-sonnet-4-5",
        kalshi_api_key: str | None = None,
    ):
        """
        Initialize the ingestion stage.

        Args:
            min_volume: Minimum contract volume for market inclusion (default: 20,000)
            selector_model: LLM model identifier for event selection
            kalshi_api_key: Optional Kalshi API key for authenticated requests
        """
        self.min_volume = min_volume
        self.selector_model = selector_model
        self.kalshi_api_key = kalshi_api_key

        # Initialize components (selector is reusable across executions)
        self.selector = EventSelector(model=selector_model)

        logger.info(
            f"IngestionStage initialized: min_volume={min_volume}, model={selector_model}"
        )

    async def execute(
        self,
        pipeline_state: dict[str, Any] | None = None,
    ) -> IngestionOutput:
        """
        Execute the ingestion stage.

        Fetches markets from Kalshi, filters and groups them, then uses
        LLM to select the 5 most interesting events for the competition.

        Args:
            pipeline_state: Optional pipeline state dict for context.
                           Currently unused but included for pipeline interface.

        Returns:
            IngestionOutput containing:
            - selected_events: List of 5 KalshiEvent objects with full market data
            - selection_reasoning: Dict mapping event ticker to selection rationale
            - diversity_score: Float 0-1 indicating topic diversity
            - categories_covered: List of categories in the selection
            - metadata: Dict with ingestion statistics

        Raises:
            IngestionStageError: If fewer than 5 events meet criteria
        """
        start_time = datetime.now(timezone.utc)

        with logfire.span("pipeline.ingestion_stage"):
            logfire.info("Starting ingestion stage execution")

            # Step 1: Fetch markets from Kalshi API
            raw_markets = await self._fetch_markets()

            # Step 2: Group markets into events
            all_events = group_markets_by_event(raw_markets)

            logfire.info(
                "Markets grouped into events",
                total_markets=len(raw_markets),
                total_events=len(all_events),
            )

            # Step 3: Validate we have enough events
            if len(all_events) < 5:
                raise IngestionStageError(
                    f"Insufficient events for selection. "
                    f"Found {len(all_events)} events with {self.min_volume}+ volume, "
                    f"need at least 5. Consider lowering the volume threshold."
                )

            # Step 4: Use LLM to select 5 events
            selection = await self.selector.select_events(all_events)

            # Step 5: Filter to selected events only
            selected_events = self._filter_to_selected(all_events, selection)

            # Step 6: Build output with metadata
            output = self._build_output(
                selected_events=selected_events,
                selection=selection,
                all_events=all_events,
                raw_markets=raw_markets,
                start_time=start_time,
            )

            logfire.info(
                "Ingestion stage completed",
                selected_count=len(output.selected_events),
                diversity_score=output.diversity_score,
                categories=output.categories_covered,
                execution_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
            )

            return output

    async def _fetch_markets(self) -> list[dict[str, Any]]:
        """
        Fetch markets from Kalshi API with volume filtering.

        Returns:
            List of raw market dictionaries meeting volume/time criteria
        """
        async with KalshiClient(api_key=self.kalshi_api_key) as client:
            markets = await client.get_markets_closing_within_24h(
                min_volume=self.min_volume,
            )

            logfire.info(
                "Fetched markets from Kalshi",
                count=len(markets),
                min_volume=self.min_volume,
            )

            return markets

    def _filter_to_selected(
        self,
        all_events: list[KalshiEvent],
        selection: EventSelection,
    ) -> list[KalshiEvent]:
        """
        Filter events to only those selected by the LLM.

        Maintains the order from the selection for consistent output.

        Args:
            all_events: All available events
            selection: LLM selection result with chosen tickers

        Returns:
            List of exactly 5 KalshiEvent objects (or fewer if LLM selected invalid tickers)
        """
        # Build lookup for O(1) access
        events_by_ticker = {event.event_ticker: event for event in all_events}

        # Select in order specified by LLM
        selected: list[KalshiEvent] = []
        for ticker in selection.selected_event_tickers:
            if ticker in events_by_ticker:
                selected.append(events_by_ticker[ticker])
            else:
                logfire.warn(
                    f"Selected ticker not found in available events: {ticker}"
                )

        # Log if we got fewer than 5 (shouldn't happen with valid LLM output)
        if len(selected) < 5:
            logfire.warn(
                f"Only {len(selected)} valid events selected, expected 5",
                valid_tickers=[e.event_ticker for e in selected],
                invalid_tickers=[
                    t for t in selection.selected_event_tickers
                    if t not in events_by_ticker
                ],
            )

        return selected

    def _build_output(
        self,
        selected_events: list[KalshiEvent],
        selection: EventSelection,
        all_events: list[KalshiEvent],
        raw_markets: list[dict[str, Any]],
        start_time: datetime,
    ) -> IngestionOutput:
        """
        Build the final IngestionOutput with all metadata.

        Args:
            selected_events: The 5 selected KalshiEvent objects
            selection: LLM selection result
            all_events: All events before selection
            raw_markets: Raw market data from API
            start_time: Stage execution start time

        Returns:
            Complete IngestionOutput object
        """
        end_time = datetime.now(timezone.utc)
        execution_ms = (end_time - start_time).total_seconds() * 1000

        # Calculate aggregate statistics
        total_volume = sum(event.total_volume for event in all_events)
        selected_volume = sum(event.total_volume for event in selected_events)
        total_market_count = sum(event.market_count for event in all_events)
        selected_market_count = sum(event.market_count for event in selected_events)

        metadata = {
            # Counts
            "events_scanned": len(all_events),
            "markets_scanned": len(raw_markets),
            "events_selected": len(selected_events),
            "markets_selected": selected_market_count,
            # Volume statistics
            "total_volume_scanned": total_volume,
            "selected_volume": selected_volume,
            "min_volume_threshold": self.min_volume,
            # Timing
            "execution_start": start_time.isoformat(),
            "execution_end": end_time.isoformat(),
            "execution_time_ms": execution_ms,
            # Configuration
            "selector_model": self.selector_model,
        }

        return IngestionOutput(
            selected_events=selected_events,
            selection_reasoning=selection.selection_reasoning,
            diversity_score=selection.diversity_score,
            categories_covered=selection.categories_covered,
            metadata=metadata,
        )


async def run_ingestion_stage(
    min_volume: int = 20_000,
    selector_model: str = "anthropic:claude-sonnet-4-5",
    kalshi_api_key: str | None = None,
) -> IngestionOutput:
    """
    Convenience function to run the ingestion stage.

    Creates and executes an IngestionStage instance with the given configuration.

    Args:
        min_volume: Minimum contract volume threshold
        selector_model: LLM model for event selection
        kalshi_api_key: Optional Kalshi API key

    Returns:
        IngestionOutput with selected events and metadata

    Example:
        output = await run_ingestion_stage()
        for event in output.selected_events:
            print(f"{event.event_ticker}: {event.total_volume} contracts")
    """
    stage = IngestionStage(
        min_volume=min_volume,
        selector_model=selector_model,
        kalshi_api_key=kalshi_api_key,
    )
    return await stage.execute()


# Export for CLI usage
if __name__ == "__main__":
    import asyncio

    async def main():
        """Run ingestion stage and display results."""
        print("=" * 80)
        print("COLISEUM - Event Ingestion Stage")
        print("=" * 80)

        try:
            output = await run_ingestion_stage()

            print(f"\nSelected {len(output.selected_events)} events:")
            print(f"Diversity Score: {output.diversity_score:.1%}")
            print(f"Categories: {', '.join(output.categories_covered)}")
            print()

            for i, event in enumerate(output.selected_events, 1):
                print(f"\n{i}. {event.event_ticker}")
                print(f"   Title: {event.title}")
                print(f"   Volume: {event.formatted_total_volume} contracts")
                print(f"   Markets: {event.market_count}")
                print(f"   Close: {event.close_time}")
                print(f"   Reason: {output.selection_reasoning.get(event.event_ticker, 'N/A')}")

                # Show first 3 markets
                for j, market in enumerate(event.markets[:3], 1):
                    print(f"      {j}. {market.yes_sub_title or market.ticker}")
                    print(f"         YES: {market.yes_bid}¢ | Volume: {market.formatted_volume}")

                if event.market_count > 3:
                    print(f"      ... and {event.market_count - 3} more markets")

            print("\n" + "=" * 80)
            print("Metadata:")
            for key, value in output.metadata.items():
                print(f"  {key}: {value}")

        except IngestionStageError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            raise

    asyncio.run(main())
