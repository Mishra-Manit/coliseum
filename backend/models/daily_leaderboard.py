"""Daily Leaderboard database model."""

from decimal import Decimal

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class DailyLeaderboard(Base, UUIDMixin):
    """Daily performance snapshot for AI models."""

    __tablename__ = "daily_leaderboards"

    # Foreign key
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date
    date = Column(Date, nullable=False)
    rank = Column(Integer, nullable=False)

    # Daily metrics
    daily_pnl = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    daily_bets = Column(Integer, nullable=False, default=0)
    daily_wins = Column(Integer, nullable=False, default=0)
    daily_losses = Column(Integer, nullable=False, default=0)

    # Cumulative metrics snapshot
    total_balance = Column(Numeric(15, 2), nullable=False)
    total_pnl = Column(Numeric(15, 2), nullable=False)
    total_roi = Column(Numeric(8, 4), nullable=False)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    model = relationship("AIModel", back_populates="daily_leaderboards")

    # Constraints
    __table_args__ = (
        UniqueConstraint("model_id", "date", name="unique_daily_leaderboard"),
        Index("idx_daily_leaderboards_date", "date"),
    )

    def __repr__(self) -> str:
        return f"<DailyLeaderboard #{self.rank} on {self.date}>"
