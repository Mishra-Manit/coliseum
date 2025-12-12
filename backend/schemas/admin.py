"""Admin API Pydantic schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class AdminEventSelectRequest(BaseSchema):
    """Request to trigger daily event selection."""

    count: int = Field(default=5, ge=1, le=10)
    date: Optional[date] = Field(
        default=None,
        description="Date to select events for (defaults to today)",
    )


class AdminEventSwapRequest(BaseSchema):
    """Request to swap an event."""

    new_kalshi_market_id: str


class AdminEventManualRequest(BaseSchema):
    """Request to manually add an event."""

    kalshi_market_id: str
    selection_date: Optional[date] = None


class AdminEventApproveRequest(BaseSchema):
    """Request to approve pending events."""

    event_ids: list[UUID]


class AdminModelResetRequest(BaseSchema):
    """Request to reset a model's balance."""

    new_balance: Decimal = Field(
        default=Decimal("100000.00"),
        ge=0,
    )
    reason: str


class AdminEventSelectResponse(BaseSchema):
    """Response from event selection."""

    events_selected: int
    event_ids: list[UUID]
    message: str


class AdminActionResponse(BaseSchema):
    """Generic admin action response."""

    success: bool
    message: str
    data: Optional[dict] = None
