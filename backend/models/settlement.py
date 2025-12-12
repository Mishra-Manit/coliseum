"""Settlement database model."""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class Settlement(Base, UUIDMixin):
    """Event settlement record."""

    __tablename__ = "settlements"

    # Foreign key
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Settlement details
    outcome = Column(String(3), nullable=False)
    kalshi_settlement_data = Column(JSONB, nullable=True)

    # Validation
    validated = Column(Boolean, nullable=False, default=False)
    validation_notes = Column(Text, nullable=True)

    # Metrics
    total_bets_settled = Column(Integer, nullable=False, default=0)
    total_pnl_distributed = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Timestamp
    settled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    event = relationship("Event", back_populates="settlement")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('YES', 'NO')",
            name="valid_settlement_outcome",
        ),
        Index("idx_settlements_settled_at", "settled_at"),
    )

    def __repr__(self) -> str:
        return f"<Settlement {self.outcome} for event {self.event_id}>"
