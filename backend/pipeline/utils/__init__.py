"""Pydantic AI agent utilities for the Coliseum pipeline.

This module provides factory functions and utilities for creating and running
Pydantic AI agents with standardized configuration, retry logic, and Logfire instrumentation.

Public API:
    - create_agent: Factory function for creating configured agents
    - run_agent: One-shot convenience wrapper for creating and running agents
    - run_agent_safe: Run agent with error handling and fallback
    - AgentConfig: Configuration model for agent settings
    - AgentResult: Result wrapper with metadata
    - AgentExecutionError: Exception raised on agent execution failures

Example:
    from pipeline.utils import create_agent, run_agent

    # Create reusable agent
    agent = create_agent(
        model="anthropic:claude-3-5-sonnet-20241022",
        output_type=MyModel,
        system_prompt="You are...",
        temperature=0.1
    )
    result = await agent.run("user prompt")

    # One-shot execution
    result = await run_agent(
        prompt="user prompt",
        output_type=str,
        system_prompt="You are...",
        model="openai:gpt-4o"
    )
"""

from .agent_factory import (
    create_agent,
    run_agent,
    run_agent_safe,
    AgentExecutionError,
)
from .types import AgentConfig, AgentResult
from .config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    MODEL_ALIASES,
    INGESTION_DEFAULTS,
    RESEARCH_DEFAULTS,
    BETTING_DEFAULTS,
    SYNTHESIS_DEFAULTS,
)

__all__ = [
    # Factory functions
    "create_agent",
    "run_agent",
    "run_agent_safe",

    # Types and models
    "AgentConfig",
    "AgentResult",

    # Exceptions
    "AgentExecutionError",

    # Configuration constants
    "DEFAULT_TEMPERATURE",
    "DEFAULT_RETRIES",
    "DEFAULT_TIMEOUT",
    "MODEL_ALIASES",
    "INGESTION_DEFAULTS",
    "RESEARCH_DEFAULTS",
    "BETTING_DEFAULTS",
    "SYNTHESIS_DEFAULTS",
]
