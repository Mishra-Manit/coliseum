"""
Stage 1: Event Ingestion

Selects exactly 5 high-quality prediction markets for the day's AI competition.

This module provides:
- KalshiClient: Async API client for fetching prediction markets
- EventSelector: LLM-powered selection of diverse, interesting events
- IngestionStage: Main orchestration class for the ingestion pipeline

Models:
- KalshiMarket: Individual market with pricing, volume, and metadata
- KalshiEvent: Event container grouping related markets
- IngestionOutput: Stage output with selected events and reasoning
- EventSelection: LLM selection result with reasoning and diversity

Usage:
    from pipeline.stages.ingestion import IngestionStage, run_ingestion_stage

    # Option 1: Using the stage class
    stage = IngestionStage(min_volume=20_000)
    output = await stage.execute()

    # Option 2: Using the convenience function
    output = await run_ingestion_stage()

    # Access results
    for event in output.selected_events:
        print(f"{event.event_ticker}: {event.title}")
        for market in event.markets:
            print(f"  - {market.ticker}: YES {market.yes_bid}¢")
"""

from .kalshi_client import (
    # Configuration
    KalshiConfig,
    # Models
    KalshiMarket,
    KalshiEvent,
    IngestionOutput,
    # Client
    KalshiClient,
    # Utilities
    group_markets_by_event,
)

from .selector import (
    EventSelector,
    EventSelection,
    SELECTION_SYSTEM_PROMPT,
)

from .main import (
    IngestionStage,
    IngestionStageError,
    run_ingestion_stage,
)


__all__ = [
    # Configuration
    "KalshiConfig",
    # Models
    "KalshiMarket",
    "KalshiEvent",
    "IngestionOutput",
    "EventSelection",
    # Classes
    "KalshiClient",
    "EventSelector",
    "IngestionStage",
    # Exceptions
    "IngestionStageError",
    # Functions
    "run_ingestion_stage",
    "group_markets_by_event",
    # Constants
    "SELECTION_SYSTEM_PROMPT",
]
