"""Daily Leaderboard database model (SQLAlchemy/PostgreSQL)."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint, Index, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.ai_model import AIModel


class DailyLeaderboard(BaseModel):
    """Daily performance snapshot for AI models."""

    __tablename__ = "daily_leaderboards"

    # Foreign key reference
    model_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Date
    leaderboard_date = Column(Date, nullable=False, index=True)
    rank = Column(Integer, nullable=False)

    # Daily metrics
    daily_pnl = Column(NUMERIC(15, 2), nullable=False, default=Decimal("0.00"))
    daily_bets = Column(Integer, nullable=False, default=0)
    daily_wins = Column(Integer, nullable=False, default=0)
    daily_losses = Column(Integer, nullable=False, default=0)

    # Cumulative metrics snapshot
    total_balance = Column(NUMERIC(15, 2), nullable=False)
    total_pnl = Column(NUMERIC(15, 2), nullable=False)
    total_roi = Column(NUMERIC(8, 4), nullable=False)

    # Relationship
    ai_model: "AIModel" = relationship("AIModel", back_populates="leaderboard_entries")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("model_id", "leaderboard_date", name="uq_leaderboard_model_date"),
        Index("ix_daily_leaderboards_model_date", "model_id", "leaderboard_date"),
        Index("ix_daily_leaderboards_date_rank", "leaderboard_date", "rank"),
    )

    def __repr__(self) -> str:
        return f"<DailyLeaderboard #{self.rank} on {self.leaderboard_date}>"
