"""Configuration defaults and model mappings for Pydantic AI agents."""

from .types import AgentConfig


# Default configuration values
DEFAULT_TEMPERATURE = 0.1
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 30.0


# Model name aliases mapping short names to full provider:model strings
MODEL_ALIASES = {
    # Anthropic models
    "claude-haiku": "anthropic:claude-haiku-4-5",
    "claude-sonnet": "anthropic:claude-sonnet-4-5"

    # OpenAI models
    "gpt-4o": "openai:gpt-4o",
    "gpt-4o-mini": "openai:gpt-4o-mini",

    # Exa AI (uses direct SDK, not Pydantic-AI model)
    # Research conducted via ExaClient in brief_generator.py

    # OpenRouter models (for betting agents - multi-provider access)
    "gpt-4o-or": "openrouter:openai/gpt-4o",
    "claude-sonnet-or": "openrouter:anthropic/claude-3.5-sonnet",
    "grok-2": "openrouter:x-ai/grok-2",
    "gemini-pro": "openrouter:google/gemini-pro-1.5",
    "llama-3.1": "openrouter:meta-llama/llama-3.1-405b",
    "mistral-large": "openrouter:mistralai/mistral-large",
    "deepseek-v2": "openrouter:deepseek/deepseek-chat",
    "qwen-max": "openrouter:qwen/qwen-max",
}


# Stage-specific default configurations
INGESTION_DEFAULTS = AgentConfig(
    model="anthropic:claude-sonnet-4-5",  # Latest Claude Sonnet for event selection
    temperature=0.2,  # Slightly higher for creative/diverse event selection
    retries=2,
    timeout=60.0,  # Allow time for thoughtful selection
)

RESEARCH_DEFAULTS = AgentConfig(
    model="exa:answer",  # Marker only - research uses ExaClient directly
    temperature=0.1,
    retries=3,  # More retries for research due to external API
    timeout=60.0,  # Longer timeout for search operations
)

BETTING_DEFAULTS = AgentConfig(
    model="openai:gpt-4o",  # Will be overridden per agent
    temperature=0.3,
    retries=2,
    timeout=120.0,  # 2 minutes for betting decisions
)

SYNTHESIS_DEFAULTS = AgentConfig(
    model="anthropic:claude-sonnet-4-5",  # Latest Claude Sonnet for synthesis
    temperature=0.1,
    retries=2,
    timeout=30.0,
)
