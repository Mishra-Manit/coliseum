"""LLM Provider and Model Enums for easy model selection and hotswapping.

This module provides enums for all supported LLM providers and their models,
making it easy to switch between different models across the codebase.
"""

from enum import StrEnum


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    FIREWORKS = "fireworks"


class OpenAIModel(StrEnum):
    """OpenAI models available via API."""

    GPT_5_2 = "gpt-5.2"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"


class AnthropicModel(StrEnum):
    """Anthropic Claude models available via API."""

    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"

class FireworksModel(StrEnum):
    """Fireworks AI models available via API."""

    LLAMA_3_3_70B_INSTRUCT = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    LLAMA_3_1_405B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-405b-instruct"
    LLAMA_3_1_70B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-70b-instruct"
    LLAMA_3_1_8B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-8b-instruct"

    # DeepSeek
    DEEPSEEK_V3_2 = "accounts/fireworks/models/deepseek-v3p2"

    # Kimi
    KIMI_K_2_5 = "accounts/fireworks/models/kimi-k2p5"


# =============================================================================
# Helper Functions
# =============================================================================


def get_model_string(model: OpenAIModel | AnthropicModel | FireworksModel) -> str:
    """Get the API model string for any supported model.

    For OpenAI models, uses the 'openai-responses:' prefix to leverage the
    Responses API, which supports built-in tools like WebSearchTool.
    """
    if isinstance(model, OpenAIModel):
        return f"openai-responses:{model.value}"
    elif isinstance(model, AnthropicModel):
        return f"anthropic:{model.value}"
    elif isinstance(model, FireworksModel):
        return f"fireworks:{model.value}"
    return model.value


def get_provider_for_model(
    model: OpenAIModel | AnthropicModel | FireworksModel,
) -> LLMProvider:
    """Determine the provider for a given model."""
    if isinstance(model, OpenAIModel):
        return LLMProvider.OPENAI
    elif isinstance(model, AnthropicModel):
        return LLMProvider.ANTHROPIC
    elif isinstance(model, FireworksModel):
        return LLMProvider.FIREWORKS
    else:
        raise ValueError(f"Unknown model type: {type(model)}")
