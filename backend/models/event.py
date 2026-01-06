"""Event database model (Beanie/MongoDB)."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List, Any, TYPE_CHECKING

from beanie import Document, Indexed, Link, BackLink
from pydantic import Field

from models.base import TimestampMixin

if TYPE_CHECKING:
    from models.event_summary import EventSummary
    from models.betting_session import BettingSession
    from models.bet import Bet
    from models.settlement import Settlement


class Event(TimestampMixin, Document):
    """Prediction market event from Kalshi."""

    # Kalshi identifiers
    kalshi_event_id: Optional[Indexed(str, unique=True)] = None
    kalshi_market_id: Optional[Indexed(str, unique=True)] = None

    # Event details
    title: str
    question: str
    current_price: Decimal = Field(default=Decimal("0.5000"))

    # Categorization
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    market_context: Optional[str] = None

    # Lifecycle
    status: Indexed(str) = Field(default="pending")  # pending, active, closed, settled
    selection_date: Indexed(date)
    close_time: Indexed(datetime)
    settlement_time: Optional[datetime] = None

    # Outcome (after settlement)
    outcome: Optional[str] = None  # YES, NO, or None

    # Engagement metrics
    viewers: int = Field(default=0)

    # Kalshi metadata (stored as dict in MongoDB)
    kalshi_data: Optional[dict] = None

    class Settings:
        name = "events"
        use_state_management = True

    def __repr__(self) -> str:
        title_preview = self.title[:50] if self.title else "Unknown"
        return f"<Event {title_preview} ({self.status})>"
