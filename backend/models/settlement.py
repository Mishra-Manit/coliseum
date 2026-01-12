"""Settlement database model (SQLAlchemy/PostgreSQL)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.event import Event


class Settlement(BaseModel):
    """Event settlement record."""

    __tablename__ = "settlements"

    # Foreign key reference (unique - one settlement per event)
    event_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    # Settlement details
    outcome = Column(String, nullable=False)  # YES or NO
    kalshi_settlement_data = Column(JSONB, nullable=True)

    # Validation
    validated = Column(Boolean, nullable=False, default=False)
    validation_notes = Column(String, nullable=True)

    # Metrics
    total_bets_settled = Column(Integer, nullable=False, default=0)
    total_pnl_distributed = Column(NUMERIC(15, 2), nullable=False, default=Decimal("0.00"))

    # Timestamp
    settled_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationship
    event: "Event" = relationship("Event", back_populates="settlement")

    def __repr__(self) -> str:
        return f"<Settlement {self.outcome} for event {self.event_id}>"
