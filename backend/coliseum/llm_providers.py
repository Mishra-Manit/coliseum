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

    # GPT-5 Series (Latest, Late 2025)
    GPT_5_2 = "gpt-5.2"
    GPT_5_1 = "gpt-5.1"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"

    # Reasoning models (O-series) - for complex reasoning tasks
    O4_MINI = "o4-mini"
    O3 = "o3"                  # Released Jan 2025
    O3_MINI = "o3-mini"        # Released Jan 2025
    O1 = "o1"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"


class AnthropicModel(StrEnum):
    """Anthropic Claude models available via API."""

    # Claude 4.5 Series
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"

class FireworksModel(StrEnum):
    """Fireworks AI models available via API."""

    # Llama 3.3 / 3.1 Series
    LLAMA_3_3_70B_INSTRUCT = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    LLAMA_3_1_405B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-405b-instruct"
    LLAMA_3_1_70B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-70b-instruct"
    LLAMA_3_1_8B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-8b-instruct"

    # Mixtral MoE models
    MIXTRAL_8X22B_INSTRUCT = "accounts/fireworks/models/mixtral-8x22b-instruct"
    MIXTRAL_8X7B_INSTRUCT = "accounts/fireworks/models/mixtral-8x7b-instruct"

    # Qwen Series
    QWEN_3_CODER_480B = "accounts/fireworks/models/qwen3-coder-480b-instruct"
    QWEN_2_5_72B_INSTRUCT = "accounts/fireworks/models/qwen2p5-72b-instruct"
    QWEN_2_5_CODER_32B = "accounts/fireworks/models/qwen2p5-coder-32b-instruct"

    # DeepSeek
    DEEPSEEK_V3_0324 = "accounts/fireworks/models/deepseek-v3-0324"
    DEEPSEEK_R1_0528 = "accounts/fireworks/models/deepseek-r1-0528"
    DEEPSEEK_V3 = "accounts/fireworks/models/deepseek-v3"
    DEEPSEEK_R1 = "accounts/fireworks/models/deepseek-r1"


# =============================================================================
# Helper Functions
# =============================================================================


def get_model_string(model: OpenAIModel | AnthropicModel | FireworksModel) -> str:
    """Get the API model string for any supported model."""
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
