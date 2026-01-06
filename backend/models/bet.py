"""Bet database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from beanie import Document, Indexed, Link, PydanticObjectId
from pydantic import Field

from models.base import TimestampMixin

if TYPE_CHECKING:
    from models.betting_session import BettingSession
    from models.ai_model import AIModel
    from models.event import Event


class Bet(Document):
    """Individual bet record."""

    # Foreign key references (stored as ObjectIds)
    session_id: Indexed(PydanticObjectId)
    model_id: Indexed(PydanticObjectId)
    event_id: Indexed(PydanticObjectId)

    # Bet details
    position: str  # YES or NO
    amount: Decimal
    price: Decimal
    shares: int

    # Settlement
    pnl: Optional[Decimal] = None
    settled: Indexed(bool) = Field(default=False)
    settled_at: Optional[datetime] = None

    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bets"
        use_state_management = True

    def __repr__(self) -> str:
        return f"<Bet {self.position} ${self.amount} @ {self.price}>"
