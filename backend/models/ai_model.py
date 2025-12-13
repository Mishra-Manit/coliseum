"""AI Model database model."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import TimestampMixin, UUIDMixin


class AIModel(Base, UUIDMixin, TimestampMixin):
    """AI model registry with balance and performance tracking."""

    __tablename__ = "ai_models"

    # Identifiers
    external_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    openrouter_model = Column(String(200), nullable=False)

    # Display properties
    color = Column(String(50), nullable=False)
    text_color = Column(String(50), nullable=False)
    avatar = Column(String(10), nullable=False)

    # Financial tracking
    balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("100000.00"),
    )
    initial_balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("100000.00"),
    )
    total_pnl = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Performance metrics
    win_count = Column(Integer, nullable=False, default=0)
    loss_count = Column(Integer, nullable=False, default=0)
    abstain_count = Column(Integer, nullable=False, default=0)
    total_bets = Column(Integer, nullable=False, default=0)

    # Relationships
    betting_sessions = relationship(
        "BettingSession",
        back_populates="model",
        lazy="dynamic",
    )
    bets = relationship(
        "Bet",
        back_populates="model",
        lazy="dynamic",
    )
    daily_leaderboards = relationship(
        "DailyLeaderboard",
        back_populates="model",
        lazy="dynamic",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("balance >= 0", name="balance_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<AIModel {self.name} (${self.balance})>"
