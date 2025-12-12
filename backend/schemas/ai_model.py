"""AI Model Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class AIModelBase(BaseSchema):
    """Base AI model schema."""

    external_id: str
    name: str
    openrouter_model: str
    color: str
    text_color: str
    avatar: str


class AIModelResponse(AIModelBase):
    """AI model response schema."""

    id: UUID
    balance: Decimal
    total_pnl: Decimal
    roi_percentage: Decimal
    win_count: int
    loss_count: int
    abstain_count: int
    total_bets: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AIModelBriefResponse(BaseSchema):
    """Brief AI model response for embedding."""

    id: UUID
    external_id: str
    name: str
    color: str
    text_color: str
    avatar: str
    balance: Decimal


class AIModelPerformanceResponse(BaseSchema):
    """AI model performance metrics."""

    id: UUID
    name: str
    balance: Decimal
    initial_balance: Decimal
    total_pnl: Decimal
    roi_percentage: Decimal
    win_count: int
    loss_count: int
    abstain_count: int
    total_bets: int
    win_rate: Optional[Decimal] = Field(
        default=None,
        description="Win rate percentage",
    )
    average_bet_size: Optional[Decimal] = Field(
        default=None,
        description="Average bet amount",
    )


class LeaderboardEntry(BaseSchema):
    """Leaderboard entry schema."""

    rank: int
    model: AIModelBriefResponse
    total_pnl: Decimal
    roi_percentage: Decimal
    win_count: int
    loss_count: int


class LeaderboardResponse(BaseSchema):
    """Leaderboard response schema."""

    entries: list[LeaderboardEntry]
    as_of: datetime
