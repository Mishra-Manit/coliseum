"""Shared tools for PydanticAI agents."""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic_ai import Agent, RunContext

logger = logging.getLogger(__name__)


def strip_cite_tokens(text: str) -> str:
    """Strip OpenAI Responses API citation tokens that leak when structured output is used.

    Handles formats with Unicode separator characters between parts, e.g.:
      □cite□turn25view0□turn23search1□  (box chars as delimiters)
      citeturn25view0turn23search1       (no delimiters)
    """
    return re.sub(r'\W{0,4}(?:file)?cite\W{0,4}(?:turn\d+\w+\W{0,4})+', '', text)


def register_get_current_time[T](agent: Agent[T, Any]) -> None:
    """Register get_current_time tool on any agent."""

    @agent.tool
    def get_current_time(ctx: RunContext[T]) -> str:
        """Get the current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()
