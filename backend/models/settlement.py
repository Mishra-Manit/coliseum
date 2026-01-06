"""Settlement database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Settlement(Document):
    """Event settlement record."""

    # Foreign key reference (unique - one settlement per event)
    event_id: Indexed(PydanticObjectId, unique=True)

    # Settlement details
    outcome: str  # YES or NO
    kalshi_settlement_data: Optional[Dict[str, Any]] = None

    # Validation
    validated: bool = Field(default=False)
    validation_notes: Optional[str] = None

    # Metrics
    total_bets_settled: int = Field(default=0)
    total_pnl_distributed: Decimal = Field(default=Decimal("0.00"))

    # Timestamp
    settled_at: Indexed(datetime) = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "settlements"
        use_state_management = True

    def __repr__(self) -> str:
        return f"<Settlement {self.outcome} for event {self.event_id}>"
