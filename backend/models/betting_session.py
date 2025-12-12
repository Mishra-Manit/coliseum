"""Betting Session database model."""

from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import TimestampMixin, UUIDMixin


class BettingSession(Base, UUIDMixin, TimestampMixin):
    """Per-model, per-event betting session."""

    __tablename__ = "betting_sessions"

    # Foreign keys
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session state
    status = Column(String(20), nullable=False, default="pending")

    # Final decision
    final_position = Column(String(10), nullable=True)
    bet_amount = Column(Numeric(15, 2), nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)

    # Reasoning
    reasoning_summary = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    event = relationship("Event", back_populates="betting_sessions")
    model = relationship("AIModel", back_populates="betting_sessions")
    messages = relationship(
        "SessionMessage",
        back_populates="session",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="SessionMessage.sequence_number",
    )
    bets = relationship(
        "Bet",
        back_populates="session",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("event_id", "model_id", name="unique_session"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="valid_session_status",
        ),
        CheckConstraint(
            "final_position IS NULL OR final_position IN ('YES', 'NO', 'ABSTAIN')",
            name="valid_position",
        ),
        Index("idx_betting_sessions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<BettingSession {self.model_id} on {self.event_id} ({self.status})>"
