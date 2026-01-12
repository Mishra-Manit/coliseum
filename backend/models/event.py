"""Event database model (SQLAlchemy/PostgreSQL)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, Date, DateTime, Index, NUMERIC
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.event_summary import EventSummary
    from models.betting_session import BettingSession
    from models.bet import Bet
    from models.settlement import Settlement


class Event(BaseModel):
    """Prediction market event from Kalshi."""

    __tablename__ = "events"

    # Kalshi identifiers
    kalshi_event_id = Column(String, unique=True, index=True, nullable=True)
    kalshi_market_id = Column(String, unique=True, index=True, nullable=True)

    # Event details
    title = Column(String, nullable=False)
    question = Column(String, nullable=False)
    current_price = Column(NUMERIC(10, 4), nullable=False, default=Decimal("0.5000"))

    # Categorization
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    market_context = Column(String, nullable=True)

    # Lifecycle
    status = Column(String, nullable=False, default="pending", index=True)
    selection_date = Column(Date, nullable=False, index=True)
    close_time = Column(DateTime(timezone=True), nullable=False, index=True)
    settlement_time = Column(DateTime(timezone=True), nullable=True)

    # Outcome (after settlement)
    outcome = Column(String, nullable=True)  # YES, NO, or None

    # Engagement metrics
    viewers = Column(Integer, nullable=False, default=0)

    # Kalshi metadata (stored as JSONB in PostgreSQL)
    kalshi_data = Column(JSONB, nullable=True)

    # Relationships
    summary: "EventSummary" = relationship(
        "EventSummary",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    betting_sessions: list["BettingSession"] = relationship(
        "BettingSession",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    bets: list["Bet"] = relationship(
        "Bet",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    settlement: "Settlement" = relationship(
        "Settlement",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_events_status_close_time", "status", "close_time"),
    )

    def __repr__(self) -> str:
        title_preview = self.title[:50] if self.title else "Unknown"
        return f"<Event {title_preview} ({self.status})>"
