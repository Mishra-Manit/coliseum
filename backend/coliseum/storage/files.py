"""Pydantic models and ID generators for opportunities and trades."""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class OpportunitySignal(BaseModel):
    """Scout-discovered opportunity."""

    # Scout fields
    id: str = Field(
        description="Unique opportunity ID with 'opp_' prefix (e.g., 'opp_a1b2c3d4'). Use generate_opportunity_id_tool() to create."
    )
    event_ticker: str = Field(
        description="Kalshi event ticker from market data (e.g., 'KXNFL-2024')"
    )
    event_title: str = Field(
        default="",
        description="Human-readable event name from Kalshi events API (e.g., 'Lowest temperature in Chicago on Mar 11, 2026?')"
    )
    market_ticker: str = Field(
        description="Kalshi market ticker from market data 'ticker' field (e.g., 'KXNFL-2024-KC-WIN')"
    )
    market_title: str = Field(
        description="Human-readable market title describing the event outcome"
    )
    subtitle: str = Field(
        default="",
        description="Additional context or specific outcome being bet on. Empty string if not applicable."
    )
    yes_price: float = Field(
        ge=0, le=1,
        description="YES contract price as decimal 0-1."
    )
    no_price: float = Field(
        ge=0, le=1,
        description="NO contract price as decimal 0-1."
    )
    close_time: datetime = Field(
        description="Market close timestamp in ISO 8601 format"
    )
    rationale: str = Field(
        description="Explanation for selecting this opportunity. MUST reference only market data."
    )
    discovered_at: datetime = Field(
        description="Timestamp when Scout discovered this"
    )
    status: str = Field(
        default="pending",
        description="Lifecycle status for the opportunity."
    )
    # Structured Scout output (populated by new prompt format)
    outcome_status: str = Field(default="", description="CONFIRMED | NEAR-DECIDED | STRONGLY FAVORED")
    risk_level: str = Field(default="", description="NEGLIGIBLE | LOW | MODERATE | HIGH")
    resolution_source: str = Field(default="", description="One sentence on resolution mechanism")
    evidence_bullets: list[str] = Field(default_factory=list, description="2-4 specific quantitative facts")
    remaining_risks: list[str] = Field(default_factory=list, description="1-3 brief risk items")
    scout_sources: list[str] = Field(default_factory=list, description="Real https:// URLs from Scout research")
    # Research fields
    research_completed_at: datetime | None = None
    research_duration_seconds: int | None = None

    # Recommendation fields
    recommendation_completed_at: datetime | None = None
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"] | None = None

    # Trader fields
    trader_decision: str = Field(default="", description="EXECUTE_BUY_YES | EXECUTE_BUY_NO | REJECT")
    trader_tldr: str = Field(default="", description="10-15 word summary from Trader agent")


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


def _generate_id(prefix: str) -> str:
    """Generate a short unique ID with the given prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


def generate_opportunity_id() -> str:
    """Generate unique opportunity ID."""
    return _generate_id("opp")


def generate_trade_id() -> str:
    """Generate unique trade execution ID."""
    return _generate_id("trade")


def generate_close_id() -> str:
    """Generate unique trade closure ID."""
    return _generate_id("close")
