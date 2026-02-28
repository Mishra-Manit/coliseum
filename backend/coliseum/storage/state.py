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


class PortfolioStats(BaseModel):
    """Current portfolio value breakdown."""

    total_value: float
    cash_balance: float
    positions_value: float


class Position(BaseModel):
    """Open position details."""

    id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    average_entry: float
    current_price: float
    opportunity_id: str | None = None


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
    state_path = _get_state_path()
    state.last_updated = datetime.now(timezone.utc)
    state_dict = state.model_dump(mode="json")

    # Same directory as target so rename is atomic on the same filesystem
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

        shutil.move(str(temp_path), str(state_path))
        logger.debug(f"Saved state to {state_path}")

    except Exception as e:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        logger.error(f"Failed to save state: {e}")
        raise


def add_seen_ticker(ticker: str) -> None:
    """Append a ticker to seen_tickers in state.yaml if not already present."""
    state = load_state()
    if ticker not in state.seen_tickers:
        state.seen_tickers.append(ticker)
        save_state(state)


def get_seen_tickers() -> list[str]:
    """Return all tickers that have been discovered by Scout."""
    return load_state().seen_tickers
