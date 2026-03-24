"""Portfolio state management with atomic writes to data/state.yaml."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from coliseum.config import get_settings

logger = logging.getLogger(__name__)


class PortfolioStats(BaseModel):
    """Current portfolio value breakdown."""

    total_value: float
    cash_balance: float
    positions_value: float

    @field_validator("total_value", "cash_balance", "positions_value")
    @classmethod
    def round_usd(cls, v: float) -> float:
        return round(v, 2)


class Position(BaseModel):
    """Open position details."""

    id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    average_entry: float
    current_price: float
    opportunity_id: str | None = None

    @field_validator("average_entry", "current_price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)


class ClosedPosition(BaseModel):
    """Closed position record -- moved here by Guardian when Kalshi confirms close."""

    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    opportunity_id: str | None = None
    closed_at: datetime | None = None
    entry_rationale: str | None = None

    @field_validator("entry_price", "exit_price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("pnl")
    @classmethod
    def round_usd(cls, v: float) -> float:
        return round(v, 2)


class PortfolioState(BaseModel):
    """Complete portfolio state matching data/state.yaml schema."""

    last_updated: datetime | None = None
    portfolio: PortfolioStats
    open_positions: list[Position] = Field(default_factory=list)
    closed_positions: list[ClosedPosition] = Field(default_factory=list)
    seen_tickers: list[str] = Field(default_factory=list)


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
    return PortfolioState(
        last_updated=None,
        portfolio=PortfolioStats(
            total_value=0.0,
            cash_balance=0.0,
            positions_value=0.0,
        ),
        open_positions=[],
    )


def load_state() -> PortfolioState:
    """Load portfolio state from data/state.yaml."""
    state_path = _get_state_path()

    if not state_path.exists():
        logger.info(f"State file not found: {state_path}. Returning default empty state.")
        return _create_default_state()

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        if not raw_data:
            logger.warning(f"Empty state file: {state_path}. Returning default state.")
            return _create_default_state()

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
    """Atomically save portfolio state to data/state.yaml."""
    from coliseum.storage._io import atomic_write, yaml_dump

    state_path = _get_state_path()
    state_dict = state.model_dump(mode="json")
    state_dict["last_updated"] = datetime.now(timezone.utc).isoformat()

    atomic_write(state_path, yaml_dump(state_dict))
    logger.debug("Saved state to %s", state_path)


def add_seen_ticker(ticker: str) -> None:
    """Append a ticker to seen_tickers in state.yaml if not already present."""
    state = load_state()
    if ticker not in state.seen_tickers:
        save_state(state.model_copy(update={"seen_tickers": [*state.seen_tickers, ticker]}))


def get_seen_tickers() -> list[str]:
    """Return all tickers that have been discovered by Scout."""
    return load_state().seen_tickers
