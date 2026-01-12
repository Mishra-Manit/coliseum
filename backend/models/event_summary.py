"""Event Summary database model (SQLAlchemy/PostgreSQL)."""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.event import Event


class EventSummary(BaseModel):
    """AI-generated summary for standardized event context."""

    __tablename__ = "event_summaries"

    # Foreign key reference (unique - one summary per event)
    event_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    # Summary content
    summary_text = Column(String, nullable=False)
    relevant_data = Column(JSONB, nullable=False, default=dict)

    # Key factors for AI reasoning
    key_factors = Column(JSONB, nullable=False, default=list)

    # Search metadata
    sources_used = Column(JSONB, nullable=False, default=list)
    search_queries = Column(JSONB, nullable=False, default=list)

    # Agent metadata
    agent_model = Column(String, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Relationship
    event: "Event" = relationship("Event", back_populates="summary")

    def __repr__(self) -> str:
        return f"<EventSummary for event {self.event_id}>"
