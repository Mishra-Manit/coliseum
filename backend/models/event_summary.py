"""Event Summary database model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database.base import Base
from models.base import UUIDMixin


class EventSummary(Base, UUIDMixin):
    """AI-generated summary for standardized event context."""

    __tablename__ = "event_summaries"

    # Foreign key
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Summary content
    summary_text = Column(Text, nullable=False)
    key_factors = Column(JSONB, nullable=False, default=list)
    recent_news = Column(JSONB, nullable=False, default=list)
    relevant_data = Column(JSONB, nullable=False, default=dict)

    # Search metadata
    sources_used = Column(JSONB, nullable=False, default=list)
    search_queries = Column(JSONB, nullable=False, default=list)

    # Agent metadata
    agent_model = Column(String(200), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    event = relationship("Event", back_populates="summary")

    def __repr__(self) -> str:
        return f"<EventSummary for event {self.event_id}>"
