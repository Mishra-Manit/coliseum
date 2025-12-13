"""Event Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class EventStatus(str, Enum):
    """Event status enum."""

    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    SETTLED = "settled"


class EventOutcome(str, Enum):
    """Event outcome enum."""

    YES = "YES"
    NO = "NO"


class EventBase(BaseSchema):
    """Base event schema."""

    title: str
    question: str
    category: str
    subcategory: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    market_context: Optional[str] = None


class EventCreate(EventBase):
    """Event creation schema."""

    kalshi_event_id: Optional[str] = None
    kalshi_market_id: Optional[str] = None
    current_price: Decimal = Field(ge=0, le=1, default=Decimal("0.5"))
    selection_date: date
    close_time: datetime


class EventResponse(EventBase):
    """Event response schema."""

    id: UUID
    kalshi_event_id: Optional[str]
    kalshi_market_id: Optional[str]
    current_price: Decimal
    status: EventStatus
    selection_date: date
    close_time: datetime
    settlement_time: Optional[datetime]
    outcome: Optional[EventOutcome]
    viewers: int
    created_at: datetime
    updated_at: datetime


class EventBriefResponse(BaseSchema):
    """Brief event response for lists."""

    id: UUID
    title: str
    question: str
    current_price: Decimal
    category: str
    status: EventStatus
    close_time: datetime
    viewers: int


class EventDetailResponse(EventResponse):
    """Detailed event response with summary."""

    summary: Optional["EventSummaryResponse"] = None
    model_positions: Optional[list["ModelPositionResponse"]] = None


class EventSummaryResponse(BaseSchema):
    """Event summary response schema."""

    id: UUID
    event_id: UUID
    summary_text: str
    relevant_data: dict[str, Any]
    sources_used: list[str]
    search_queries: list[str]
    agent_model: Optional[str]
    created_at: datetime


class ModelPositionResponse(BaseSchema):
    """Model position on an event."""

    model_id: UUID
    model_name: str
    model_color: str
    model_avatar: str
    position: Optional[str]  # YES, NO, ABSTAIN, or None if pending
    shares: int = 0
    avg_price: Decimal = Decimal("0")
    pnl: Optional[Decimal] = None


# Avoid circular import
EventDetailResponse.model_rebuild()
