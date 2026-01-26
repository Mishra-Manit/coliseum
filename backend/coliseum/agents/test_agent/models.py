"""Data models for the Test Agent."""

from pydantic import BaseModel, Field

from coliseum.config import Settings
from coliseum.services.telegram import TelegramClient


class TestAgentDependencies(BaseModel):
    """Dependencies injected into Test Agent."""

    model_config = {"arbitrary_types_allowed": True}

    telegram_client: TelegramClient
    config: Settings
    data_dir: str | None = None  # Optional custom data directory (for testing)
    dry_run: bool = False  # If True, skip actually sending Telegram alerts


class InterestSelection(BaseModel):
    """Agent's decision on most interesting opportunity."""

    selected_opportunity_id: str = Field(
        description="ID of the selected opportunity (e.g., 'opp_abc123')"
    )
    interest_reason: str = Field(
        max_length=200,
        description="Single sentence explaining why this opportunity is interesting (max 200 chars)",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in this selection (0.0 to 1.0)",
    )


class TestAgentOutput(BaseModel):
    """Complete output from Test Agent."""

    selection: InterestSelection = Field(
        description="The opportunity selected by the agent with reasoning"
    )
    telegram_sent: bool = Field(
        description="Whether the Telegram alert was sent successfully"
    )
    telegram_message_id: int | None = Field(
        default=None,
        description="Telegram message ID if alert was sent successfully",
    )
    opportunities_evaluated: int = Field(
        description="Total number of opportunities considered"
    )
