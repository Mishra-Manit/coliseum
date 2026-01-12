"""Session Message database model (SQLAlchemy/PostgreSQL)."""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, ForeignKey, Index, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.betting_session import BettingSession


class SessionMessage(BaseModel):
    """AI reasoning message during a betting session."""

    __tablename__ = "session_messages"

    # Foreign key reference
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("betting_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message content
    message_type = Column(String, nullable=False, default="reasoning")  # reasoning, action, system
    content = Column(String, nullable=False)

    # Associated action (if any)
    action_type = Column(String, nullable=True)  # BUY, SELL
    action_amount = Column(NUMERIC(15, 2), nullable=True)
    action_shares = Column(Integer, nullable=True)
    action_price = Column(NUMERIC(10, 4), nullable=True)

    # Sequencing
    sequence_number = Column(Integer, nullable=False)

    # Relationship
    session: "BettingSession" = relationship("BettingSession", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("ix_session_messages_session_created", "session_id", "created_at"),
        Index("ix_session_messages_session_seq", "session_id", "sequence_number"),
    )

    def __repr__(self) -> str:
        return f"<SessionMessage #{self.sequence_number} ({self.message_type})>"
