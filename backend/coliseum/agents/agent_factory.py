"""Generic agent factory for managing singleton agent instances."""

import logging
import os
from typing import Callable, Generic, TypeVar

from pydantic_ai import Agent

from coliseum.config import get_settings

logger = logging.getLogger(__name__)

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT")


class AgentFactory(Generic[DepsT, OutputT]):
    """Factory for managing singleton agent instances with consistent initialization."""

    def __init__(
        self,
        create_fn: Callable[[], Agent[DepsT, OutputT]],
        register_tools_fn: Callable[[Agent[DepsT, OutputT]], None] | None = None,
    ):
        """Initialize the agent factory.

        Args:
            create_fn: Function that creates a new agent instance
            register_tools_fn: Optional function to register tools on the agent
        """
        self._create_fn = create_fn
        self._register_tools_fn = register_tools_fn
        self._agent: Agent[DepsT, OutputT] | None = None

    def get_agent(self) -> Agent[DepsT, OutputT]:
        """Get or create the singleton agent instance."""
        if self._agent is None:
            self._setup_api_keys()
            self._agent = self._create_fn()
            if self._register_tools_fn is not None:
                self._register_tools_fn(self._agent)
        return self._agent

    def _setup_api_keys(self) -> None:
        """Setup OpenAI API key from settings if available."""
        settings = get_settings()
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
