"""WebSocket Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import Field

from schemas.common import BaseSchema


class WSClientAction(str, Enum):
    """Client WebSocket actions."""

    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class WSServerMessageType(str, Enum):
    """Server WebSocket message types."""

    PRICE_UPDATE = "price_update"
    MESSAGE = "message"
    BET = "bet"
    SETTLEMENT = "settlement"
    VIEWERS = "viewers"
    SESSION_STATUS = "session_status"
    ERROR = "error"


class WSClientMessage(BaseSchema):
    """Message from client to server."""

    action: WSClientAction
    event_id: UUID


class WSPriceUpdate(BaseSchema):
    """Price update message."""

    type: str = WSServerMessageType.PRICE_UPDATE
    event_id: UUID
    price: Decimal
    timestamp: datetime


class WSReasoningMessage(BaseSchema):
    """AI reasoning message."""

    type: str = WSServerMessageType.MESSAGE
    event_id: UUID
    session_id: UUID
    data: dict[str, Any]


class WSBetMessage(BaseSchema):
    """Bet placement message."""

    type: str = WSServerMessageType.BET
    event_id: UUID
    data: dict[str, Any]


class WSSettlementMessage(BaseSchema):
    """Settlement message."""

    type: str = WSServerMessageType.SETTLEMENT
    event_id: UUID
    data: dict[str, Any]


class WSViewerCountMessage(BaseSchema):
    """Viewer count update message."""

    type: str = WSServerMessageType.VIEWERS
    event_id: UUID
    count: int
    timestamp: datetime


class WSSessionStatusMessage(BaseSchema):
    """Session status update message."""

    type: str = WSServerMessageType.SESSION_STATUS
    event_id: UUID
    session_id: UUID
    model_id: UUID
    status: str
    final_position: Optional[str] = None


class WSErrorMessage(BaseSchema):
    """Error message."""

    type: str = WSServerMessageType.ERROR
    message: str
    code: Optional[str] = None


# Union type for all server messages
WSServerMessage = Union[
    WSPriceUpdate,
    WSReasoningMessage,
    WSBetMessage,
    WSSettlementMessage,
    WSViewerCountMessage,
    WSSessionStatusMessage,
    WSErrorMessage,
]
