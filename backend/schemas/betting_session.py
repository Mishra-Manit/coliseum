"""Betting Session Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class SessionStatus(str, Enum):
    """Session status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionPosition(str, Enum):
    """Session final position enum."""

    YES = "YES"
    NO = "NO"
    ABSTAIN = "ABSTAIN"


class BettingSessionBase(BaseSchema):
    """Base betting session schema."""

    event_id: UUID
    model_id: UUID


class BettingSessionResponse(BettingSessionBase):
    """Betting session response schema."""

    id: UUID
    status: SessionStatus
    final_position: Optional[SessionPosition]
    bet_amount: Optional[Decimal]
    confidence_score: Optional[Decimal]
    reasoning_summary: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class BettingSessionDetailResponse(BettingSessionResponse):
    """Detailed betting session with model info."""

    model_name: str
    model_color: str
    model_avatar: str
    event_title: str
    messages_count: int = 0


class MessageActionType(str, Enum):
    """Message action type enum."""

    BUY = "BUY"
    SELL = "SELL"


class MessageType(str, Enum):
    """Message type enum."""

    REASONING = "reasoning"
    ACTION = "action"
    SYSTEM = "system"


class SessionMessageAction(BaseSchema):
    """Action details in a session message."""

    type: MessageActionType
    amount: Decimal
    shares: int
    price: Decimal


class SessionMessageResponse(BaseSchema):
    """Session message response schema."""

    id: UUID
    session_id: UUID
    message_type: MessageType
    content: str
    action: Optional[SessionMessageAction] = None
    sequence_number: int
    created_at: datetime

    # Model info for display
    model_id: Optional[UUID] = None
    model_name: Optional[str] = None
    model_color: Optional[str] = None
    model_avatar: Optional[str] = None


class SessionMessageCreate(BaseSchema):
    """Session message creation schema (internal use)."""

    message_type: MessageType = MessageType.REASONING
    content: str
    action_type: Optional[MessageActionType] = None
    action_amount: Optional[Decimal] = None
    action_shares: Optional[int] = None
    action_price: Optional[Decimal] = None
