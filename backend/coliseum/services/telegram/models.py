"""Telegram notification models."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class NotificationResult(BaseModel):
    """Notification delivery result."""

    success: bool
    message_id: int | None = None
    recipient: str
    sent_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error: str | None = None
    retry_count: int = 0

    def __str__(self) -> str:
        """Human-readable status."""
        if self.success:
            return f"Sent to {self.recipient} (msg_id: {self.message_id})"
        return f"Failed to {self.recipient}: {self.error}"
