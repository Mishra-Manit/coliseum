"""Generic agent factory for managing singleton agent instances."""

import logging
from typing import Any, Callable, Generic, TypeVar

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.memory.context import load_kalshi_mechanics

logger = logging.getLogger(__name__)

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT")


def create_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None = None,
    reasoning_effort: str = "medium",
    builtin_tools: list[Any] | None = None,
    prepend_mechanics: bool = True,
) -> Agent[DepsT, OutputT]:
    """Create a PydanticAI agent with standard Coliseum configuration."""
    system_prompt = f"{load_kalshi_mechanics()}\n\n{prompt}" if prepend_mechanics else prompt
    kwargs: dict[str, Any] = {
        "model": get_model_string(OpenAIModel.GPT_5_4),
        "output_type": output_type,
        "system_prompt": system_prompt,
        "model_settings": OpenAIResponsesModelSettings(openai_reasoning_effort=reasoning_effort),
    }
    if deps_type is not None:
        kwargs["deps_type"] = deps_type
    if builtin_tools:
        kwargs["builtin_tools"] = builtin_tools
    return Agent(**kwargs)


class AgentFactory(Generic[DepsT, OutputT]):
    """Factory for managing singleton agent instances with consistent initialization."""

    def __init__(
        self,
        create_fn: Callable[[], Agent[DepsT, OutputT]],
        register_tools_fn: Callable[[Agent[DepsT, OutputT]], None] | None = None,
    ):
        """Wire creation and optional tool registration for the singleton agent."""
        self._create_fn = create_fn
        self._register_tools_fn = register_tools_fn
        self._agent: Agent[DepsT, OutputT] | None = None

    def get_agent(self) -> Agent[DepsT, OutputT]:
        """Get or create the singleton agent instance."""
        if self._agent is None:
            self._agent = self._create_fn()
            if self._register_tools_fn is not None:
                self._register_tools_fn(self._agent)
        return self._agent
