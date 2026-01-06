"""Session Message database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class SessionMessage(Document):
    """AI reasoning message during a betting session."""

    # Foreign key reference
    session_id: Indexed(PydanticObjectId)

    # Message content
    message_type: str = Field(default="reasoning")  # reasoning, action, system
    content: str

    # Associated action (if any)
    action_type: Optional[str] = None  # BUY, SELL
    action_amount: Optional[Decimal] = None
    action_shares: Optional[int] = None
    action_price: Optional[Decimal] = None

    # Sequencing
    sequence_number: int

    # Timestamp
    created_at: Indexed(datetime) = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "session_messages"
        use_state_management = True

    def __repr__(self) -> str:
        return f"<SessionMessage #{self.sequence_number} ({self.message_type})>"
