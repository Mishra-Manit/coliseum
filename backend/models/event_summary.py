"""Event Summary database model (Beanie/MongoDB)."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class EventSummary(Document):
    """AI-generated summary for standardized event context."""

    # Foreign key reference (unique - one summary per event)
    event_id: Indexed(PydanticObjectId, unique=True)

    # Summary content
    summary_text: str
    relevant_data: Dict[str, Any] = Field(default_factory=dict)

    # Key factors for AI reasoning
    key_factors: List[Dict[str, Any]] = Field(default_factory=list)

    # Search metadata
    sources_used: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)

    # Agent metadata
    agent_model: Optional[str] = None
    generation_time_ms: Optional[int] = None

    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "event_summaries"
        use_state_management = True

    def __repr__(self) -> str:
        return f"<EventSummary for event {self.event_id}>"
