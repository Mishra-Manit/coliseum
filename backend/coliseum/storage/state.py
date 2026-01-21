"""Portfolio state management with atomic writes to data/state.yaml."""

import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from coliseum.config import get_settings

logger = logging.getLogger(__name__)


# Status type for opportunity lifecycle
OpportunityStatus = Literal[
    "pending", "researching", "recommended", "traded", "expired", "skipped"
]


# ============================================================================
# Pydantic Models
# ============================================================================


class PortfolioStats(BaseModel):
    """Current portfolio value breakdown."""

    total_value: float
    cash_balance: float
    positions_value: float


class DailyStats(BaseModel):
    """Daily performance metrics."""

    date: str | None  # ISO date (YYYY-MM-DD)
    starting_value: float
    current_pnl: float
    current_pnl_pct: float
    trades_today: int


class Position(BaseModel):
    """Open position details."""

    id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    average_entry: float
    current_price: float
    unrealized_pnl: float


class RiskStatus(BaseModel):
    """Risk management status flags."""

    daily_loss_limit_hit: bool
    trading_halted: bool
    capital_at_risk_pct: float


class SeenMarket(BaseModel):
    """Tracked market to prevent duplicate Scout discovery. Auto-cleaned after close_time."""

    opportunity_id: str
    discovered_at: datetime
    close_time: datetime
    status: OpportunityStatus = "pending"


class PortfolioState(BaseModel):
    """Complete portfolio state - matches data/state.yaml schema."""

    last_updated: datetime | None = None
    portfolio: PortfolioStats
    daily_stats: DailyStats
    open_positions: list[Position] = Field(default_factory=list)
    risk_status: RiskStatus
    seen_markets: dict[str, SeenMarket] = Field(default_factory=dict)


# ============================================================================
# Helper Functions
# ============================================================================


def get_data_dir() -> Path:
    """Get the data directory path from settings."""
    settings = get_settings()
    data_dir = settings.data_dir

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}. "
            "Run 'python -m coliseum init' to create it."
        )

    return data_dir


def _get_state_path() -> Path:
    """Get the path to state.yaml."""
    return get_data_dir() / "state.yaml"


def _create_default_state() -> PortfolioState:
    """Create a default empty portfolio state."""
    settings = get_settings()
    initial_value = settings.trading.initial_bankroll

    return PortfolioState(
        last_updated=None,
        portfolio=PortfolioStats(
            total_value=initial_value,
            cash_balance=initial_value,
            positions_value=0.0,
        ),
        daily_stats=DailyStats(
            date=None,
            starting_value=initial_value,
            current_pnl=0.0,
            current_pnl_pct=0.0,
            trades_today=0,
        ),
        open_positions=[],
        risk_status=RiskStatus(
            daily_loss_limit_hit=False,
            trading_halted=False,
            capital_at_risk_pct=0.0,
        ),
    )


# ============================================================================
# Public API
# ============================================================================


def load_state() -> PortfolioState:
    """Load portfolio state from data/state.yaml."""
    state_path = _get_state_path()

    # If state file doesn't exist, return default
    if not state_path.exists():
        logger.info(
            f"State file not found: {state_path}. Returning default empty state."
        )
        return _create_default_state()

    # Load and parse YAML
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        if not raw_data:
            logger.warning(f"Empty state file: {state_path}. Returning default state.")
            return _create_default_state()

        # Parse into Pydantic model
        state = PortfolioState(**raw_data)
        logger.debug(f"Loaded state from {state_path}")
        return state

    except yaml.YAMLError as e:
        logger.error(f"Corrupted YAML in state file: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        raise


def save_state(state: PortfolioState) -> None:
    """Atomically save portfolio state to data/state.yaml.

    This uses a tempfile → rename pattern to ensure atomic writes.
    If the process crashes mid-write, the original state.yaml remains intact.
    """
    state_path = _get_state_path()

    # Update timestamp automatically
    state.last_updated = datetime.utcnow()

    # Convert Pydantic model to dict, handling datetime serialization
    state_dict = state.model_dump(mode="json")

    # Write to temporary file in same directory (atomic rename requirement)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=state_path.parent,
            delete=False,
            suffix=".yaml",
            encoding="utf-8",
        ) as temp_file:
            yaml.dump(
                state_dict,
                temp_file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            temp_path = Path(temp_file.name)

        # Atomic rename
        shutil.move(str(temp_path), str(state_path))
        logger.debug(f"Saved state to {state_path}")

    except Exception as e:
        # Clean up temp file if it exists
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        logger.error(f"Failed to save state: {e}")
        raise


# ============================================================================
# Seen Markets Management
# ============================================================================


def mark_market_seen(
    market_ticker: str,
    opportunity_id: str,
    close_time: datetime,
    status: OpportunityStatus = "pending",
) -> None:
    """Mark a market as seen by Scout to prevent duplicate discovery."""
    state = load_state()
    
    # Only add if not already seen (preserve original discovery)
    if market_ticker in state.seen_markets:
        logger.debug(f"Market {market_ticker} already seen, skipping")
        return
    
    state.seen_markets[market_ticker] = SeenMarket(
        opportunity_id=opportunity_id,
        discovered_at=datetime.now(timezone.utc),
        close_time=close_time,
        status=status,
    )
    
    save_state(state)
    logger.info(f"Marked market as seen: {market_ticker} (opp: {opportunity_id})")


def is_market_seen(market_ticker: str) -> bool:
    """Check if a market has already been discovered."""
    state = load_state()
    return market_ticker in state.seen_markets


def get_seen_market(market_ticker: str) -> SeenMarket | None:
    """Get the SeenMarket entry for a ticker, if it exists."""
    state = load_state()
    return state.seen_markets.get(market_ticker)


def get_seen_tickers() -> list[str]:
    """Get list of all currently tracked market tickers."""
    state = load_state()
    return list(state.seen_markets.keys())


def update_market_status(market_ticker: str, status: OpportunityStatus) -> bool:
    """Update the status of a seen market. Returns True if updated."""
    state = load_state()
    
    if market_ticker not in state.seen_markets:
        logger.warning(f"Cannot update status: market {market_ticker} not in seen_markets")
        return False
    
    state.seen_markets[market_ticker].status = status
    save_state(state)
    logger.info(f"Updated market {market_ticker} status to: {status}")
    return True


def cleanup_seen_markets() -> int:
    """Remove expired markets from seen_markets. Returns count removed."""
    state = load_state()
    now = datetime.now(timezone.utc)
    
    # Find expired tickers
    expired_tickers = [
        ticker
        for ticker, market in state.seen_markets.items()
        if market.close_time < now
    ]
    
    if not expired_tickers:
        logger.debug("No expired markets to clean up")
        return 0
    
    # Remove expired entries
    for ticker in expired_tickers:
        del state.seen_markets[ticker]
    
    save_state(state)
    logger.info(f"Cleaned up {len(expired_tickers)} expired markets from seen_markets")
    
    return len(expired_tickers)
