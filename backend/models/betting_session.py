"""Betting Session database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from models.base import TimestampMixin

if TYPE_CHECKING:
    from models.event import Event
    from models.ai_model import AIModel
    from models.session_message import SessionMessage
    from models.bet import Bet


class BettingSession(TimestampMixin, Document):
    """Per-model, per-event betting session."""

    # Foreign key references (stored as ObjectIds)
    event_id: Indexed(PydanticObjectId)
    model_id: Indexed(PydanticObjectId)

    # Session state
    status: Indexed(str) = Field(default="pending")  # pending, running, completed, failed

    # Final decision
    final_position: Optional[str] = None  # YES, NO, ABSTAIN
    bet_amount: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None

    # Reasoning
    reasoning_summary: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "betting_sessions"
        use_state_management = True
        # Compound unique index on event_id + model_id
        indexes = [
            [("event_id", 1), ("model_id", 1)],
        ]

    def __repr__(self) -> str:
        return f"<BettingSession {self.model_id} on {self.event_id} ({self.status})>"
