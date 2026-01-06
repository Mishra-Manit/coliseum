"""Daily Leaderboard database model (Beanie/MongoDB)."""

from datetime import date, datetime, timezone
from decimal import Decimal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class DailyLeaderboard(Document):
    """Daily performance snapshot for AI models."""

    # Foreign key reference
    model_id: Indexed(PydanticObjectId)

    # Date
    leaderboard_date: Indexed(date)
    rank: int

    # Daily metrics
    daily_pnl: Decimal = Field(default=Decimal("0.00"))
    daily_bets: int = Field(default=0)
    daily_wins: int = Field(default=0)
    daily_losses: int = Field(default=0)

    # Cumulative metrics snapshot
    total_balance: Decimal
    total_pnl: Decimal
    total_roi: Decimal

    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "daily_leaderboards"
        use_state_management = True
        # Compound unique index on model_id + date
        indexes = [
            [("model_id", 1), ("leaderboard_date", 1)],
        ]

    def __repr__(self) -> str:
        return f"<DailyLeaderboard #{self.rank} on {self.leaderboard_date}>"
