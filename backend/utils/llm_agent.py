"""
Utilities for creating instrumented pydantic-ai agents with OpenRouter.

This module provides factory functions for creating pydantic-ai agents
configured to use OpenRouter as the LLM provider. All agents are
automatically instrumented by Logfire for observability.
"""

import logging
from typing import Optional, Type, TypeVar, Union

from pydantic import BaseModel
from pydantic_ai import Agent

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T", bound=Union[BaseModel, str])


def _resolve_output_type(output_type: Optional[Type[T]]) -> Type[Union[BaseModel, str]]:
    """Validate and resolve the output type for the agent."""
    if output_type is None or output_type is str:
        return str
    if issubclass(output_type, BaseModel):
        return output_type
    raise ValueError(
        f"output_type must be str or a Pydantic BaseModel subclass, got {output_type}"
    )


def _default_system_prompt(output_type: Type[Union[BaseModel, str]]) -> str:
    """Generate a default system prompt based on output type."""
    if output_type is str:
        return "You are a helpful AI assistant."
    return (
        "You are a helpful AI assistant that extracts and structures data into "
        f"{output_type.__name__} format."
    )


def create_agent(
    model: str,
    output_type: Optional[Type[T]] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    retries: int = 2,
    timeout: Optional[float] = None,
) -> Agent[None, T]:
    """
    Create a pydantic-ai Agent configured for OpenRouter.

    Args:
        model: OpenRouter model identifier (e.g., "openai:anthropic/claude-3.5-sonnet")
        output_type: Expected output type (str or Pydantic BaseModel subclass)
        system_prompt: Custom system prompt (auto-generated if not provided)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        retries: Number of retry attempts on failure
        timeout: Request timeout in seconds

    Returns:
        Agent: Configured pydantic-ai agent with Logfire instrumentation

    Example:
        # Simple string output
        agent = create_agent(
            model="openai:anthropic/claude-3.5-sonnet",
            system_prompt="You are a prediction market analyst."
        )
        result = await agent.run("Analyze this market...")

        # Structured output
        class PredictionAnalysis(BaseModel):
            confidence: float
            reasoning: str

        agent = create_agent(
            model="openai:google/gemini-2.0-flash-exp",
            output_type=PredictionAnalysis
        )
        result = await agent.run("Analyze this prediction...")
    """
    resolved_output_type = _resolve_output_type(output_type)
    prompt = system_prompt or _default_system_prompt(resolved_output_type)

    model_settings = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if timeout is not None:
        model_settings["timeout"] = timeout

    agent = Agent(
        model=model,
        result_type=resolved_output_type,
        system_prompt=prompt,
        retries=retries,
        model_settings=model_settings,
    )

    logger.debug(
        "Created OpenRouter agent: model=%s, output_type=%s, temperature=%s, "
        "max_tokens=%s, retries=%s, timeout=%s",
        model,
        getattr(resolved_output_type, "__name__", str(resolved_output_type)),
        temperature,
        max_tokens,
        retries,
        timeout,
    )

    return agent


async def run_agent(
    prompt: str,
    model: str,
    output_type: Optional[Type[T]] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    retries: int = 2,
    timeout: Optional[float] = None,
) -> T:
    """
    Create an agent, invoke it with prompt, and return the result.

    This is a convenience function that combines agent creation and execution.

    Args:
        prompt: User prompt to send to the agent
        model: OpenRouter model identifier
        output_type: Expected output type
        system_prompt: Custom system prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        retries: Number of retry attempts
        timeout: Request timeout in seconds

    Returns:
        The agent's output (str or structured BaseModel instance)

    Example:
        result = await run_agent(
            prompt="What is the probability of this event?",
            model="openai:anthropic/claude-3.5-sonnet",
            temperature=0.3
        )
    """
    agent = create_agent(
        model=model,
        output_type=output_type,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        retries=retries,
        timeout=timeout,
    )

    result = await agent.run(prompt)
    return result.data
