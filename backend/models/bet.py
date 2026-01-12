"""Bet database model (SQLAlchemy/PostgreSQL)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.betting_session import BettingSession
    from models.ai_model import AIModel
    from models.event import Event


class Bet(BaseModel):
    """Individual bet record."""

    __tablename__ = "bets"

    # Foreign key references
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("betting_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    model_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Bet details
    position = Column(String, nullable=False)  # YES or NO
    amount = Column(NUMERIC(15, 2), nullable=False)
    price = Column(NUMERIC(10, 4), nullable=False)
    shares = Column(Integer, nullable=False)

    # Settlement
    pnl = Column(NUMERIC(15, 2), nullable=True)
    settled = Column(Boolean, nullable=False, default=False, index=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session: "BettingSession" = relationship("BettingSession", back_populates="bets")
    ai_model: "AIModel" = relationship("AIModel", back_populates="bets")
    event: "Event" = relationship("Event", back_populates="bets")

    # Indexes
    __table_args__ = (
        Index("ix_bets_model_created", "model_id", "created_at"),
        Index("ix_bets_event_model", "event_id", "model_id"),
    )

    def __repr__(self) -> str:
        return f"<Bet {self.position} ${self.amount} @ {self.price}>"
