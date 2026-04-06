"""Opportunity domain model and ID generator."""

from datetime import datetime
from typing import Literal
from coliseum.domain._utils import generate_prefixed_id

from pydantic import BaseModel, Field


class OpportunitySignal(BaseModel):
    """Scout-discovered opportunity."""

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
    outcome_status: str = Field(default="", description="CONFIRMED | NEAR-DECIDED | STRONGLY FAVORED")
    risk_level: str = Field(default="", description="NEGLIGIBLE | LOW | MODERATE | HIGH")
    resolution_source: str = Field(default="", description="One sentence on resolution mechanism")
    evidence_bullets: list[str] = Field(default_factory=list, description="2-4 specific quantitative facts")
    remaining_risks: list[str] = Field(default_factory=list, description="1-3 brief risk items")
    scout_sources: list[str] = Field(default_factory=list, description="Real https:// URLs from Scout research")
    research_completed_at: datetime | None = None
    research_duration_seconds: int | None = None
    recommendation_completed_at: datetime | None = None
    action: Literal["BUY_YES", "BUY_NO", "ABSTAIN"] | None = None
    trader_decision: str = Field(default="", description="EXECUTE_BUY_YES | EXECUTE_BUY_NO | REJECT")
    trader_tldr: str = Field(default="", description="10-15 word summary from Trader agent")


def generate_opportunity_id() -> str:
    """Generate unique opportunity ID."""
    return generate_prefixed_id("opp")
