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
from pydantic_ai.models.xai import XaiModel as PydanticAIXaiModel, XaiModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.xai import XaiProvider

from coliseum.config import get_settings
from coliseum.llm_providers import GrokModel, OpenAIModel
from coliseum.memory.context import load_kalshi_mechanics

logger = logging.getLogger(__name__)

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT")

_openai_provider: OpenAIProvider | None = None
_xai_provider: XaiProvider | None = None


def _get_openai_provider() -> OpenAIProvider:
    """Return the shared OpenAI provider, creating it on first call."""
    global _openai_provider
    if _openai_provider is None:
        _openai_provider = OpenAIProvider(openai_client=AsyncOpenAI(max_retries=2))
    return _openai_provider


def _get_xai_provider() -> XaiProvider:
    """Return the shared xAI provider, creating it on first call."""
    global _xai_provider
    if _xai_provider is None:
        settings = get_settings()
        _xai_provider = XaiProvider(api_key=settings.xai_api_key)
    return _xai_provider


def _build_system_prompt(prompt: str, prepend_mechanics: bool) -> str:
    """Prepend Kalshi mechanics context to the prompt if requested."""
    if prepend_mechanics:
        return f"{load_kalshi_mechanics()}\n\n{prompt}"
    return prompt


def _create_openai_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None,
    reasoning_effort: str,
    builtin_tools: list[Any] | None,
    prepend_mechanics: bool,
    use_responses_api: bool,
) -> Agent[DepsT, OutputT]:
    """Create an agent using the OpenAI provider."""
    system_prompt = _build_system_prompt(prompt, prepend_mechanics)
    model_name = OpenAIModel.GPT_5_4
    provider = _get_openai_provider()

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


def _create_xai_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None,
    builtin_tools: list[Any] | None,
    prepend_mechanics: bool,
    max_tokens: int | None = None,
) -> Agent[DepsT, OutputT]:
    """Create an agent using the xAI Grok provider."""
    system_prompt = _build_system_prompt(prompt, prepend_mechanics)
    model = PydanticAIXaiModel(GrokModel.GROK_4_20_REASONING, provider=_get_xai_provider())
    settings_kwargs: dict[str, Any] = {"timeout": 300}
    if max_tokens is not None:
        settings_kwargs["max_tokens"] = max_tokens
    model_settings = XaiModelSettings(**settings_kwargs)

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


def create_agent(
    prompt: str,
    output_type: type[OutputT],
    deps_type: type[DepsT] | None = None,
    reasoning_effort: str = "medium",
    builtin_tools: list[Any] | None = None,
    prepend_mechanics: bool = True,
    use_responses_api: bool = True,
    max_tokens: int | None = None,
) -> Agent[DepsT, OutputT]:
    """Create a PydanticAI agent with standard Coliseum configuration.

    Routes to the appropriate provider based on config.yaml llm.provider setting.
    """
    settings = get_settings()

    if settings.llm.provider == "xai":
        return _create_xai_agent(
            prompt, output_type, deps_type, builtin_tools, prepend_mechanics, max_tokens
        )

    return _create_openai_agent(
        prompt,
        output_type,
        deps_type,
        reasoning_effort,
        builtin_tools,
        prepend_mechanics,
        use_responses_api,
    )


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
