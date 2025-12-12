"""Price History database model."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class PriceHistory(Base, UUIDMixin):
    """Historical price data for events."""

    __tablename__ = "price_history"

    # Foreign key
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Price data
    price = Column(Numeric(5, 4), nullable=False)
    volume = Column(Integer, nullable=True)
    source = Column(String(20), nullable=False, default="kalshi")

    # Timestamp
    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    event = relationship("Event", back_populates="price_history")

    # Indexes
    __table_args__ = (
        Index("idx_price_history_recorded_at", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<PriceHistory {self.price} @ {self.recorded_at}>"
