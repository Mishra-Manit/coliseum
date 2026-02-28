"""Shared tools for PydanticAI agents."""

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic_ai import Agent, RunContext

logger = logging.getLogger(__name__)


def register_get_current_time[T](agent: Agent[T, Any]) -> None:
    """Register get_current_time tool on any agent."""

    @agent.tool
    def get_current_time(ctx: RunContext[T]) -> str:
        """Get the current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()
