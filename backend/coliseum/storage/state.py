"""Portfolio state models and data directory accessor."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from coliseum.config import get_settings


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
