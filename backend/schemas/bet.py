"""Bet Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class BetPosition(str, Enum):
    """Bet position enum."""

    YES = "YES"
    NO = "NO"


class BetBase(BaseSchema):
    """Base bet schema."""

    position: BetPosition
    amount: Decimal = Field(gt=0)


class BetCreate(BetBase):
    """Bet creation schema."""

    session_id: UUID
    model_id: UUID
    event_id: UUID
    price: Decimal = Field(gt=0, lt=1)


class BetResponse(BetBase):
    """Bet response schema."""

    id: UUID
    session_id: UUID
    model_id: UUID
    event_id: UUID
    price: Decimal
    shares: int
    pnl: Optional[Decimal]
    settled: bool
    settled_at: Optional[datetime]
    created_at: datetime


class BetDetailResponse(BetResponse):
    """Detailed bet response with model and event info."""

    model_name: str
    model_color: str
    model_avatar: str
    event_title: str


class SettlementResponse(BaseSchema):
    """Settlement response schema."""

    id: UUID
    event_id: UUID
    outcome: str
    validated: bool
    validation_notes: Optional[str]
    total_bets_settled: int
    total_pnl_distributed: Decimal
    settled_at: datetime


class SettlementResultResponse(BaseSchema):
    """Settlement result for broadcasting."""

    outcome: str
    results: list["ModelSettlementResult"]
    timestamp: datetime


class ModelSettlementResult(BaseSchema):
    """Individual model settlement result."""

    model_id: UUID
    model_name: str
    position: Optional[str]  # YES, NO, ABSTAIN
    pnl: Decimal
    new_balance: Decimal


# Rebuild for forward references
SettlementResultResponse.model_rebuild()
