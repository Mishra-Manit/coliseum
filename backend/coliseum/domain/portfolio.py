"""Portfolio state domain models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    close_time: datetime | None = None

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
    """Complete portfolio state."""

    last_updated: datetime | None = None
    portfolio: PortfolioStats
    open_positions: list[Position] = Field(default_factory=list)
    closed_positions: list[ClosedPosition] = Field(default_factory=list)
    seen_tickers: list[str] = Field(default_factory=list)
