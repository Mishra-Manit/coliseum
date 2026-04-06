"""Trade execution and closure domain models."""

from datetime import datetime
from typing import Literal
from coliseum.domain._utils import generate_prefixed_id

from pydantic import BaseModel, field_validator


class TradeExecution(BaseModel):
    """Trade execution record."""

    id: str
    position_id: str | None
    opportunity_id: str
    market_ticker: str
    side: Literal["YES", "NO"]
    action: Literal["BUY", "SELL"]
    contracts: int
    price: float
    total: float
    paper: bool
    executed_at: datetime

    @field_validator("price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("total")
    @classmethod
    def round_total(cls, v: float) -> float:
        return round(v, 2)


class TradeClose(BaseModel):
    """Position closure record written by Guardian when a market resolves."""

    id: str
    opportunity_id: str | None
    market_ticker: str
    side: Literal["YES", "NO"]
    contracts: int
    entry_price: float
    exit_price: float
    pnl: float
    entry_rationale: str | None
    closed_at: datetime

    @field_validator("entry_price", "exit_price")
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("pnl")
    @classmethod
    def round_usd(cls, v: float) -> float:
        return round(v, 2)


def generate_trade_id() -> str:
    """Generate unique trade execution ID."""
    return generate_prefixed_id("trade")


def generate_close_id() -> str:
    """Generate unique trade closure ID."""
    return generate_prefixed_id("close")
