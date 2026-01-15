"""
Kalshi API Client

Production-ready async client for fetching prediction markets from Kalshi.

Features:
- Async HTTP client with connection pooling
- Cursor-based pagination with automatic handling
- Retry logic with exponential backoff for rate limits and server errors
- Filtering by volume threshold and close time

Methods:
- get_markets_closing_within_24h(min_volume): Fetch high-volume markets closing soon
- get_event_markets(event_ticker): Fetch all markets for a specific event

Error Handling:
- Implements retry with exponential backoff for transient failures
- Raises appropriate exceptions for permanent failures
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Optional

import httpx
import logfire
from pydantic import BaseModel, Field, field_validator, model_validator

# Configure module logger
logger = logging.getLogger(__name__)


class KalshiConfig:
    """Configuration constants for the Kalshi API client."""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    TIMEOUT_SECONDS = 30.0
    MAX_API_LIMIT = 1000
    DEFAULT_PAGE_SIZE = 200
    SECONDS_IN_24H = 86400
    DEFAULT_MIN_VOLUME = 20_000  # Minimum contracts traded
    DEFAULT_FETCH_LIMIT = 10_000

    # Connection pooling settings
    MAX_CONNECTIONS = 100
    MAX_KEEPALIVE_CONNECTIONS = 20

    # Retry configuration
    MAX_RETRIES = 3
    RATE_LIMIT_WAIT_SECONDS = 5
    SERVER_ERROR_WAIT_SECONDS = 2


class KalshiMarket(BaseModel):
    """
    Pydantic model for a Kalshi prediction market.

    Captures all fields returned by the Kalshi API for a market,
    enabling full data preservation as it flows through the pipeline.

    Attributes:
        ticker: Unique market identifier (e.g., "KXNFLGAME-26JAN10GBCHI-GB")
        event_ticker: Parent event identifier
        title: Event title / question
        yes_sub_title: Outcome description for YES side
        yes_bid: Current YES bid price in cents (0-100)
        yes_ask: Current YES ask price in cents (0-100)
        no_bid: Current NO bid price in cents (0-100)
        no_ask: Current NO ask price in cents (0-100)
        volume: Total trading volume in contracts
        close_time: ISO 8601 timestamp when market closes
        status: Market status (open, closed, settled)
        category: Market category (often empty, requires LLM classification)
    """

    # Core identifiers
    ticker: str = Field(description="Unique market identifier")
    event_ticker: str = Field(default="", description="Parent event identifier")

    # Market information
    title: str = Field(default="", description="Event title or question")
    subtitle: str = Field(default="", description="Market subtitle")
    yes_sub_title: str = Field(default="", description="YES outcome description")
    no_sub_title: str = Field(default="", description="NO outcome description")

    # Pricing data (in cents, 0-100 representing probability percentage)
    yes_bid: int = Field(default=0, ge=0, le=100, description="YES bid price in cents")
    yes_ask: int = Field(default=0, ge=0, le=100, description="YES ask price in cents")
    no_bid: int = Field(default=0, ge=0, le=100, description="NO bid price in cents")
    no_ask: int = Field(default=0, ge=0, le=100, description="NO ask price in cents")
    last_price: int = Field(default=0, ge=0, le=100, description="Last traded price")

    # Volume and liquidity
    volume: int = Field(default=0, ge=0, description="Trading volume in contracts")
    volume_24h: int = Field(default=0, ge=0, description="24h trading volume")
    liquidity: int = Field(default=0, ge=0, description="Market liquidity in cents")
    open_interest: int = Field(default=0, ge=0, description="Open interest in contracts")

    # Timing
    close_time: str = Field(default="", description="ISO 8601 close timestamp")
    expiration_time: str = Field(default="", description="ISO 8601 expiration timestamp")
    open_time: str = Field(default="", description="ISO 8601 open timestamp")

    # Status and type
    status: str = Field(default="open", description="Market status")
    market_type: str = Field(default="binary", description="Market type")
    result: str = Field(default="", description="Settlement result if resolved")

    # Classification
    category: str = Field(default="", description="Market category")
    series_ticker: str = Field(default="", description="Series ticker")

    # Rules and resolution
    rules_primary: str = Field(default="", description="Primary resolution rules")
    rules_secondary: str = Field(default="", description="Secondary resolution rules")
    settlement_timer_seconds: int = Field(default=0, description="Settlement timer")

    # Additional metadata
    floor_strike: float | None = Field(default=None, description="Floor strike price")
    cap_strike: float | None = Field(default=None, description="Cap strike price")
    tick_size: int = Field(default=1, description="Minimum price increment")
    risk_limit_cents: int = Field(default=0, description="Risk limit in cents")
    strike_type: str = Field(default="", description="Strike type")
    settlement_value: int | None = Field(default=None, description="Settlement value")
    expected_expiration_time: str = Field(default="", description="Expected expiration")
    custom_strike: str | None = Field(default=None, description="Custom strike value")
    can_close_early: bool = Field(default=False, description="Early close allowed")
    notional_value: int = Field(default=100, description="Notional value per contract")
    response_price_units: str = Field(default="cents", description="Price unit type")
    previous_yes_bid: int = Field(default=0, description="Previous YES bid")
    previous_yes_ask: int = Field(default=0, description="Previous YES ask")
    previous_price: int = Field(default=0, description="Previous last price")

    class Config:
        extra = "allow"  # Allow additional fields from API

    @property
    def formatted_close_time(self) -> str:
        """Format close time for display."""
        if not self.close_time:
            return "N/A"
        try:
            dt = datetime.fromisoformat(self.close_time.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %I:%M%p")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse close_time '{self.close_time}': {e}")
            return self.close_time[:16] if len(self.close_time) >= 16 else self.close_time

    @property
    def formatted_volume(self) -> str:
        """Format volume for display (in contracts)."""
        if self.volume >= 1_000_000:
            return f"{self.volume / 1_000_000:.1f}M"
        elif self.volume >= 1_000:
            return f"{self.volume / 1_000:.1f}K"
        return f"{self.volume}"

    @property
    def yes_probability(self) -> float:
        """Calculate YES probability as decimal (0.0 to 1.0)."""
        mid_price = (self.yes_bid + self.yes_ask) / 2 if self.yes_ask else self.yes_bid
        return mid_price / 100.0

    @property
    def is_uncertain(self) -> bool:
        """Check if market outcome is uncertain (prices near 50%)."""
        prob = self.yes_probability
        return 0.25 <= prob <= 0.75


class KalshiEvent(BaseModel):
    """
    Pydantic model for a Kalshi event containing multiple markets.

    An event groups related markets together (e.g., an NFL game with
    different betting lines, or an election with multiple candidates).

    Attributes:
        event_ticker: Unique event identifier
        title: Event title/name
        category: Event category
        markets: List of markets belonging to this event
        total_volume: Sum of volume across all markets
        close_time: Earliest close time among markets
    """

    event_ticker: str = Field(description="Unique event identifier")
    title: str = Field(default="", description="Event title")
    category: str = Field(default="", description="Event category")
    markets: list[KalshiMarket] = Field(
        default_factory=list, description="Markets in this event"
    )
    total_volume: int = Field(default=0, ge=0, description="Total volume across markets")
    close_time: str = Field(default="", description="Earliest market close time")
    market_count: int = Field(default=0, ge=0, description="Number of markets")

    @model_validator(mode="after")
    def compute_aggregates(self) -> "KalshiEvent":
        """Compute aggregate fields from markets after initialization."""
        if self.markets:
            # Sum total volume across all markets
            self.total_volume = sum(m.volume for m in self.markets)
            self.market_count = len(self.markets)

            # Find earliest close time
            close_times = [m.close_time for m in self.markets if m.close_time]
            if close_times:
                self.close_time = min(close_times)

            # Use first market's title and category if not set
            if not self.title and self.markets[0].title:
                self.title = self.markets[0].title
            if not self.category and self.markets[0].category:
                self.category = self.markets[0].category

        return self

    @property
    def formatted_total_volume(self) -> str:
        """Format total volume for display."""
        if self.total_volume >= 1_000_000:
            return f"{self.total_volume / 1_000_000:.1f}M"
        elif self.total_volume >= 1_000:
            return f"{self.total_volume / 1_000:.1f}K"
        return f"{self.total_volume}"

    @property
    def average_uncertainty(self) -> float:
        """Calculate average uncertainty across markets (higher = more uncertain)."""
        if not self.markets:
            return 0.0
        uncertainties = []
        for m in self.markets:
            prob = m.yes_probability
            # Uncertainty is highest at 0.5, lowest at 0 or 1
            uncertainty = 1.0 - abs(prob - 0.5) * 2
            uncertainties.append(uncertainty)
        return sum(uncertainties) / len(uncertainties)


class IngestionOutput(BaseModel):
    """
    Output model for the ingestion stage.

    Contains the 5 selected events with full Kalshi data,
    selection reasoning, and metadata about the ingestion process.
    """

    selected_events: list[KalshiEvent] = Field(
        description="Exactly 5 selected events with full market data"
    )
    selection_reasoning: dict[str, str] = Field(
        default_factory=dict, description="Event ticker to selection reason mapping"
    )
    diversity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Topic diversity score"
    )
    categories_covered: list[str] = Field(
        default_factory=list, description="Categories represented in selection"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Ingestion metadata (events_scanned, markets_scanned, etc.)",
    )

    @field_validator("selected_events")
    @classmethod
    def validate_event_count(cls, v: list[KalshiEvent]) -> list[KalshiEvent]:
        """Ensure exactly 5 events are selected."""
        if len(v) != 5:
            logger.warning(f"Expected 5 events, got {len(v)}")
        return v


class KalshiClient:
    """
    Async client for the Kalshi prediction market API.

    Provides methods to fetch markets with pagination, filtering,
    and retry logic for robust production use.

    Usage:
        async with KalshiClient() as client:
            markets = await client.get_markets_closing_within_24h(min_volume=20_000)
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Kalshi API client.

        Args:
            api_key: Optional API key for authenticated requests.
                     Most read operations work without authentication.
        """
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

        logger.info("Initialized KalshiClient")

    async def __aenter__(self) -> "KalshiClient":
        """Context manager entry - create HTTP client."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Configure connection pooling for high-performance requests
        limits = httpx.Limits(
            max_connections=KalshiConfig.MAX_CONNECTIONS,
            max_keepalive_connections=KalshiConfig.MAX_KEEPALIVE_CONNECTIONS,
        )

        self._client = httpx.AsyncClient(
            base_url=KalshiConfig.BASE_URL,
            headers=headers,
            timeout=KalshiConfig.TIMEOUT_SECONDS,
            limits=limits,
        )

        logfire.info("KalshiClient HTTP session opened")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit - close HTTP client."""
        if self._client:
            await self._client.aclose()
            logfire.info("KalshiClient HTTP session closed")

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, ensuring it's initialized."""
        if self._client is None:
            raise RuntimeError(
                "KalshiClient must be used as async context manager. "
                "Use: async with KalshiClient() as client: ..."
            )
        return self._client

    async def _paginate(
        self,
        endpoint: str,
        params: dict[str, Any],
        limit: int,
        result_key: str = "markets",
    ) -> list[dict[str, Any]]:
        """
        Generic pagination handler for Kalshi API endpoints.

        Handles cursor-based pagination, error handling, and automatic retries
        for transient failures (rate limits, server errors).

        Args:
            endpoint: API endpoint path (e.g., "markets", "events")
            params: Query parameters for the request
            limit: Maximum number of items to fetch
            result_key: Key in response JSON containing the results array

        Returns:
            List of items from the API, up to the specified limit

        Raises:
            httpx.HTTPStatusError: For non-retryable HTTP errors
        """
        all_items: list[dict[str, Any]] = []
        cursor: str | None = None
        retry_count = 0

        while True:
            # Add cursor to params if present (for subsequent pages)
            current_params = params.copy()
            if cursor:
                current_params["cursor"] = cursor

            try:
                response = await self.client.get(endpoint, params=current_params)
                response.raise_for_status()

                # Reset retry count on success
                retry_count = 0

                # Parse response
                data = response.json()
                items = data.get(result_key, [])
                all_items.extend(items)

                logger.debug(
                    f"Fetched {len(items)} items from {endpoint} (total: {len(all_items)})"
                )

                # Check pagination - continue if cursor present and under limit
                cursor = data.get("cursor")
                if not cursor or len(all_items) >= limit:
                    break

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit - wait and retry
                    retry_count += 1
                    if retry_count >= KalshiConfig.MAX_RETRIES:
                        logfire.error("Max retries exceeded for rate limiting")
                        break
                    logfire.warn(
                        f"Rate limit exceeded, waiting {KalshiConfig.RATE_LIMIT_WAIT_SECONDS}s "
                        f"(retry {retry_count}/{KalshiConfig.MAX_RETRIES})"
                    )
                    await asyncio.sleep(KalshiConfig.RATE_LIMIT_WAIT_SECONDS)
                    continue

                elif e.response.status_code >= 500:
                    # Server error - retry with backoff
                    retry_count += 1
                    if retry_count >= KalshiConfig.MAX_RETRIES:
                        logfire.error(
                            f"Max retries exceeded for server errors: {e.response.status_code}"
                        )
                        break
                    wait_time = KalshiConfig.SERVER_ERROR_WAIT_SECONDS * retry_count
                    logfire.warn(
                        f"Server error {e.response.status_code}, waiting {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                else:
                    # Client error (4xx except 429) - don't retry
                    logfire.error(
                        f"HTTP error {e.response.status_code}: {e.response.text}"
                    )
                    break

            except httpx.TimeoutException:
                retry_count += 1
                if retry_count >= KalshiConfig.MAX_RETRIES:
                    logfire.error("Max retries exceeded for timeouts")
                    break
                logfire.warn(f"Request timeout, retrying ({retry_count}/{KalshiConfig.MAX_RETRIES})")
                await asyncio.sleep(KalshiConfig.SERVER_ERROR_WAIT_SECONDS)
                continue

            except httpx.RequestError as e:
                logfire.error(f"Network error: {e}")
                break

        return all_items[:limit]

    async def get_markets_closing_within_24h(
        self,
        min_volume: int = KalshiConfig.DEFAULT_MIN_VOLUME,
        limit: int = KalshiConfig.DEFAULT_FETCH_LIMIT,
        status: str = "open",
    ) -> list[dict[str, Any]]:
        """
        Fetch markets closing within the next 24 hours with minimum volume threshold.

        Uses the API's time filtering to get markets with close times
        between now and 24 hours from now, then filters by volume.

        Args:
            min_volume: Minimum trading volume in contracts (default: 20,000)
            limit: Maximum number of markets to return (default: 10,000)
            status: Market status filter (default: "open")

        Returns:
            List of market dictionaries meeting the criteria, sorted by volume descending
        """
        # Calculate time range: now to 24 hours from now
        current_time = int(time.time())
        time_24h = current_time + KalshiConfig.SECONDS_IN_24H

        params = {
            "limit": min(limit, KalshiConfig.MAX_API_LIMIT),
            "status": status,
            "min_close_ts": current_time,
            "max_close_ts": time_24h,
        }

        with logfire.span("kalshi.get_markets_closing_within_24h"):
            logfire.info(
                "Fetching markets closing within 24h",
                min_volume=min_volume,
                limit=limit,
            )

            # Fetch all markets in time range
            all_markets = await self._paginate("markets", params, limit, "markets")

            # Filter by minimum volume
            filtered_markets = [m for m in all_markets if m.get("volume", 0) >= min_volume]

            # Sort by volume descending
            filtered_markets.sort(key=lambda m: m.get("volume", 0), reverse=True)

            logfire.info(
                "Markets fetched and filtered",
                total_fetched=len(all_markets),
                after_volume_filter=len(filtered_markets),
                min_volume_threshold=min_volume,
            )

            return filtered_markets

    async def get_event_markets(self, event_ticker: str) -> list[dict[str, Any]]:
        """
        Fetch all markets for a specific event.

        Args:
            event_ticker: Unique event identifier

        Returns:
            List of market dictionaries for the event
        """
        logfire.info(f"Fetching markets for event: {event_ticker}")

        try:
            response = await self.client.get(f"events/{event_ticker}/markets")
            response.raise_for_status()
            data = response.json()
            markets = data.get("markets", [])

            logfire.info(
                f"Retrieved {len(markets)} markets for event {event_ticker}"
            )
            return markets

        except httpx.HTTPStatusError as e:
            logfire.error(
                f"Error fetching markets for event {event_ticker}: {e.response.status_code}"
            )
            return []

    async def get_events(
        self,
        limit: int = 100,
        status: str = "open",
        with_nested_markets: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Fetch events from Kalshi API.

        Args:
            limit: Maximum number of events to return (default: 100)
            status: Filter by event status (default: "open")
            with_nested_markets: Include nested market data (default: False)

        Returns:
            List of event dictionaries from the API
        """
        params = {
            "limit": min(limit, KalshiConfig.DEFAULT_PAGE_SIZE),
            "status": status,
            "with_nested_markets": str(with_nested_markets).lower(),
        }

        logfire.info(f"Fetching events with status={status}, limit={limit}")
        return await self._paginate("events", params, limit, "events")


def group_markets_by_event(
    markets: list[dict[str, Any]],
) -> list[KalshiEvent]:
    """
    Group raw market dictionaries into KalshiEvent objects.

    Takes a flat list of markets and groups them by event_ticker,
    creating KalshiEvent objects with aggregated data.

    Args:
        markets: List of raw market dictionaries from Kalshi API

    Returns:
        List of KalshiEvent objects, sorted by total volume descending
    """
    from collections import defaultdict

    # Group markets by event ticker
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for market in markets:
        event_ticker = market.get("event_ticker", "UNKNOWN")
        grouped[event_ticker].append(market)

    # Convert to KalshiEvent objects
    events: list[KalshiEvent] = []
    for event_ticker, market_dicts in grouped.items():
        # Convert market dicts to KalshiMarket models
        kalshi_markets = []
        for m in market_dicts:
            try:
                kalshi_market = KalshiMarket.model_validate(m)
                kalshi_markets.append(kalshi_market)
            except Exception as e:
                logger.warning(f"Failed to parse market {m.get('ticker', 'unknown')}: {e}")
                continue

        if kalshi_markets:
            event = KalshiEvent(
                event_ticker=event_ticker,
                markets=kalshi_markets,
            )
            events.append(event)

    # Sort by total volume descending
    events.sort(key=lambda e: e.total_volume, reverse=True)

    logfire.info(
        "Markets grouped by event",
        total_markets=len(markets),
        total_events=len(events),
    )

    return events
