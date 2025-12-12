"""Bet database model."""

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class Bet(Base, UUIDMixin):
    """Individual bet record."""

    __tablename__ = "bets"

    # Foreign keys
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("betting_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Bet details
    position = Column(String(3), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    price = Column(Numeric(5, 4), nullable=False)
    shares = Column(Integer, nullable=False)

    # Settlement
    pnl = Column(Numeric(15, 2), nullable=True)
    settled = Column(Boolean, nullable=False, default=False)
    settled_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session = relationship("BettingSession", back_populates="bets")
    model = relationship("AIModel", back_populates="bets")
    event = relationship("Event", back_populates="bets")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "position IN ('YES', 'NO')",
            name="valid_bet_position",
        ),
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint(
            "price > 0 AND price < 1",
            name="valid_bet_price",
        ),
        Index("idx_bets_settled", "settled"),
    )

    def __repr__(self) -> str:
        return f"<Bet {self.position} ${self.amount} @ {self.price}>"
