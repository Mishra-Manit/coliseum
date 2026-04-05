"""Decision log: structured record of every BUY/SKIP decision with reasoning."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DecisionEntry(BaseModel):
    """One trading decision record."""

    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    opportunity_id: str = ""
    ticker: str = ""
    action: str = ""
    price: float | None = None
    contracts: int = 0
    confidence: float = 0.0
    reasoning: str = ""
    tldr: str = ""
    execution_status: str = ""
    outcome: str | None = None
