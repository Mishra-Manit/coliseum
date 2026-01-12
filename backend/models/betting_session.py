"""Betting Session database model (SQLAlchemy/PostgreSQL)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.event import Event
    from models.ai_model import AIModel
    from models.session_message import SessionMessage
    from models.bet import Bet


class BettingSession(BaseModel):
    """Per-model, per-event betting session."""

    __tablename__ = "betting_sessions"

    # Foreign key references
    event_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    model_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Session state
    status = Column(String, nullable=False, default="pending", index=True)

    # Final decision
    final_position = Column(String, nullable=True)  # YES, NO, ABSTAIN
    bet_amount = Column(NUMERIC(15, 2), nullable=True)
    confidence_score = Column(NUMERIC(5, 4), nullable=True)

    # Reasoning
    reasoning_summary = Column(String, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    event: "Event" = relationship("Event", back_populates="betting_sessions")
    ai_model: "AIModel" = relationship("AIModel", back_populates="betting_sessions")
    messages: list["SessionMessage"] = relationship(
        "SessionMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    bets: list["Bet"] = relationship(
        "Bet",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("event_id", "model_id", name="uq_session_event_model"),
        Index("ix_betting_sessions_event_model", "event_id", "model_id"),
    )

    def __repr__(self) -> str:
        return f"<BettingSession {self.model_id} on {self.event_id} ({self.status})>"
