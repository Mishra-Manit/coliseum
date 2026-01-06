"""AI Model database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from beanie import Document, Indexed
from pydantic import Field

from models.base import TimestampMixin

if TYPE_CHECKING:
    from models.betting_session import BettingSession
    from models.bet import Bet
    from models.daily_leaderboard import DailyLeaderboard


class AIModel(TimestampMixin, Document):
    """AI model registry with balance and performance tracking."""

    # Identifiers
    external_id: Indexed(str, unique=True)
    name: str
    openrouter_model: str

    # Display properties
    color: str
    text_color: str
    avatar: str

    # Financial tracking
    balance: Decimal = Field(default=Decimal("100000.00"))
    initial_balance: Decimal = Field(default=Decimal("100000.00"))
    total_pnl: Decimal = Field(default=Decimal("0.00"))

    # Performance metrics
    win_count: int = Field(default=0)
    loss_count: int = Field(default=0)
    abstain_count: int = Field(default=0)
    total_bets: int = Field(default=0)
    roi_percentage: Decimal = Field(default=Decimal("0.00"))

    # Status
    is_active: bool = Field(default=True)

    class Settings:
        name = "ai_models"
        use_state_management = True

    def __repr__(self) -> str:
        return f"<AIModel {self.name} (${self.balance})>"
