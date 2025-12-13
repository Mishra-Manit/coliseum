"""Event database model."""

from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import TimestampMixin, UUIDMixin


class Event(Base, UUIDMixin, TimestampMixin):
    """Prediction market event from Kalshi."""

    __tablename__ = "events"

    # Kalshi identifiers
    kalshi_event_id = Column(String(100), unique=True, nullable=True, index=True)
    kalshi_market_id = Column(String(100), unique=True, nullable=True, index=True)

    # Event details
    title = Column(String(500), nullable=False)
    question = Column(String(1000), nullable=False)
    current_price = Column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.5000"),
    )

    # Categorization
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    market_context = Column(Text, nullable=True)

    # Lifecycle
    status = Column(String(20), nullable=False, default="pending")
    selection_date = Column(Date, nullable=False)
    close_time = Column(DateTime(timezone=True), nullable=False)
    settlement_time = Column(DateTime(timezone=True), nullable=True)

    # Outcome (after settlement)
    outcome = Column(String(10), nullable=True)

    # Engagement metrics
    viewers = Column(Integer, nullable=False, default=0)

    # Kalshi metadata
    kalshi_data = Column(JSONB, nullable=True)

    # Relationships
    summary = relationship(
        "EventSummary",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )
    betting_sessions = relationship(
        "BettingSession",
        back_populates="event",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    bets = relationship(
        "Bet",
        back_populates="event",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    settlement = relationship(
        "Settlement",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'closed', 'settled')",
            name="valid_status",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('YES', 'NO')",
            name="valid_outcome",
        ),
        CheckConstraint(
            "current_price >= 0 AND current_price <= 1",
            name="valid_price",
        ),
        Index("idx_events_status", "status"),
        Index("idx_events_selection_date", "selection_date"),
        Index("idx_events_close_time", "close_time"),
    )

    def __repr__(self) -> str:
        return f"<Event {self.title[:50]} ({self.status})>"
