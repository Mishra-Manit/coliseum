"""AI Model database model (SQLAlchemy/PostgreSQL)."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Integer, Boolean, Index, NUMERIC
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.betting_session import BettingSession
    from models.bet import Bet
    from models.daily_leaderboard import DailyLeaderboard


class AIModel(BaseModel):
    """AI model registry with balance and performance tracking."""

    __tablename__ = "ai_models"

    # Identifiers
    external_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    openrouter_model = Column(String, nullable=False)

    # Display properties
    color = Column(String, nullable=False)
    text_color = Column(String, nullable=False)
    avatar = Column(String, nullable=False)

    # Financial tracking
    balance = Column(NUMERIC(15, 2), nullable=False, default=Decimal("100000.00"))
    initial_balance = Column(NUMERIC(15, 2), nullable=False, default=Decimal("100000.00"))
    total_pnl = Column(NUMERIC(15, 2), nullable=False, default=Decimal("0.00"))

    # Performance metrics
    win_count = Column(Integer, nullable=False, default=0)
    loss_count = Column(Integer, nullable=False, default=0)
    abstain_count = Column(Integer, nullable=False, default=0)
    total_bets = Column(Integer, nullable=False, default=0)
    roi_percentage = Column(NUMERIC(8, 4), nullable=False, default=Decimal("0.00"))

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    betting_sessions: list["BettingSession"] = relationship(
        "BettingSession",
        back_populates="ai_model",
        cascade="all, delete-orphan"
    )
    bets: list["Bet"] = relationship(
        "Bet",
        back_populates="ai_model",
        cascade="all, delete-orphan"
    )
    leaderboard_entries: list["DailyLeaderboard"] = relationship(
        "DailyLeaderboard",
        back_populates="ai_model",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIModel {self.name} (${self.balance})>"
