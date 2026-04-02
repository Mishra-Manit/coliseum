"""Generic agent factory for managing singleton agent instances."""

import logging
from typing import Any, Callable, Generic, TypeVar

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import (
    OpenAIModel as PydanticAIChatModel,
    OpenAIResponsesModel,
    OpenAIChatModelSettings,
    OpenAIResponsesModelSettings,
)
from pydantic_ai.providers.openai import OpenAIProvider

from coliseum.llm_providers import OpenAIModel
from coliseum.memory.context import load_kalshi_mechanics

logger = logging.getLogger(__name__)

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT")

# Lazily initialized — the API key is loaded from .env at runtime, not at import time.
_openai_provider: OpenAIProvider | None = None


def _get_provider() -> OpenAIProvider:
    """Return the shared OpenAI provider, creating it on first call.

    max_retries=0 surfaces errors immediately instead of silently retrying for
    minutes on 5xx/429 during time-sensitive pipeline runs.
    """
    global _openai_provider
    if _openai_provider is None:
        _openai_provider = OpenAIProvider(openai_client=AsyncOpenAI(max_retries=0))
    return _openai_provider


def create_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None = None,
    reasoning_effort: str = "medium",
    builtin_tools: list[Any] | None = None,
    prepend_mechanics: bool = True,
    use_responses_api: bool = True,
) -> Agent[DepsT, OutputT]:
    """Create a PydanticAI agent with standard Coliseum configuration.

    Set use_responses_api=False for agents that don't need WebSearchTool
    """
    if prepend_mechanics:
        system_prompt = f"{load_kalshi_mechanics()}\n\n{prompt}"
    else:
        system_prompt = prompt
    model_name = OpenAIModel.GPT_5_4
    provider = _get_provider()

    if use_responses_api:
        model = OpenAIResponsesModel(model_name, provider=provider)
        model_settings: OpenAIResponsesModelSettings | OpenAIChatModelSettings = (
            OpenAIResponsesModelSettings(
                openai_reasoning_effort=reasoning_effort,
                timeout=300,
            )
        )
    else:
        model = PydanticAIChatModel(model_name, provider=provider)
        # reasoning_effort cannot be combined with function tools on /v1/chat/completions
        # for gpt-5.4 — OpenAI returns 400. Omit it; structured output still works fine.
        model_settings = OpenAIChatModelSettings(timeout=120)

    kwargs: dict[str, Any] = {
        "model": model,
        "output_type": output_type,
        "system_prompt": system_prompt,
        "model_settings": model_settings,
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
