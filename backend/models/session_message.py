"""Session Message database model."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class SessionMessage(Base, UUIDMixin):
    """AI reasoning message during a betting session."""

    __tablename__ = "session_messages"

    # Foreign key
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("betting_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    message_type = Column(String(20), nullable=False, default="reasoning")
    content = Column(Text, nullable=False)

    # Associated action (if any)
    action_type = Column(String(10), nullable=True)
    action_amount = Column(Numeric(15, 2), nullable=True)
    action_shares = Column(Integer, nullable=True)
    action_price = Column(Numeric(5, 4), nullable=True)

    # Sequencing
    sequence_number = Column(Integer, nullable=False)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session = relationship("BettingSession", back_populates="messages")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "message_type IN ('reasoning', 'action', 'system')",
            name="valid_message_type",
        ),
        CheckConstraint(
            "action_type IS NULL OR action_type IN ('BUY', 'SELL')",
            name="valid_action_type",
        ),
        Index("idx_session_messages_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SessionMessage #{self.sequence_number} ({self.message_type})>"
