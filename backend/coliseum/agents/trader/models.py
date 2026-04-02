"""Data models for the Trader agent."""

from typing import Literal

from pydantic import BaseModel, Field

from coliseum.config import Settings
from coliseum.services.kalshi.client import KalshiClient


class TraderDependencies(BaseModel):
    """Dependencies injected into Trader agent."""

    model_config = {"arbitrary_types_allowed": True}

    kalshi_client: KalshiClient
    config: Settings


class TraderDecision(BaseModel):
    """Final trading decision made by the agent."""

    action: Literal["EXECUTE_BUY_YES", "EXECUTE_BUY_NO", "REJECT"] = Field(
        description="Final decision: EXECUTE_BUY_YES to buy YES contracts, EXECUTE_BUY_NO to buy NO contracts, or REJECT to skip this trade"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in the decision (0.0 to 1.0). Higher values indicate stronger conviction.",
    )
    reasoning: str = Field(
        description="Detailed explanation of the decision and risk assessment"
    )


class OrderResult(BaseModel):
    """Result from order execution attempt."""

    order_id: str | None = None
    fill_price: float | None = None  # Average fill price in decimal (0.0-1.0)
    contracts_filled: int = 0
    total_cost_usd: float = 0.0
    status: Literal["filled", "partial", "cancelled", "rejected", "error"] = Field(
        description="Final order status"
    )
    error_message: str | None = None


class TraderOutput(BaseModel):
    """Complete output from Trader agent."""

    decision: TraderDecision = Field(
        description="The final trading decision made by the agent"
    )
    tldr: str = Field(
        description="A punchy 10-20 word notification that combines event-specific context with your reasoning. Lead with what's actually happening in the real world, then briefly say why that makes the trade good (or bad). Be conversational like texting a friend. Never use generic trading jargon like 'flip risk', 'execution range', 'no reversal path', or 'in band'."
    )
    trader_notes: str | None = Field(
        default=None,
        description="Key observations about this trade: critical factors influencing the decision and potential risks to watch.",
    )
    order_id: str | None = Field(
        default=None,
        description="Kalshi order ID if order was placed (None if REJECTED or skipped)",
    )
    fill_price: float | None = Field(
        default=None,
        description="Average fill price in decimal (0.0-1.0) if order was filled",
    )
    contracts_filled: int = Field(
        default=0,
        description="Number of contracts filled (0 if no order placed or not filled)",
    )
    total_cost_usd: float = Field(
        default=0.0,
        description="Total cost in USD for the filled position",
    )
    execution_status: Literal[
        "pending", "filled", "partial", "cancelled", "rejected", "skipped", "paper"
    ] = Field(
        default="pending",
        description="Set by execution logic, not the agent.",
    )