"""Portfolio state management with atomic writes.

This module manages the single source of truth for the Coliseum portfolio state,
stored in data/state.yaml. All reads and writes use Pydantic models for type safety,
and writes are atomic to prevent corruption.
"""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from coliseum.config import get_settings

logger = logging.getLogger(__name__)


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


class PortfolioState(BaseModel):
    """Complete portfolio state - matches data/state.yaml schema."""

    last_updated: datetime | None = None
    portfolio: PortfolioStats
    daily_stats: DailyStats
    open_positions: list[Position] = Field(default_factory=list)
    risk_status: RiskStatus


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
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to save state: {e}")
        raise
