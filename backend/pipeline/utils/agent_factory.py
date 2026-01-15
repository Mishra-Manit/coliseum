"""Factory functions for creating and running Pydantic AI agents."""

import time
from typing import TypeVar, Type, Union, get_origin
from pydantic import BaseModel
from pydantic_ai import Agent
import logfire

from .types import OutputT, AgentResult
from .config import DEFAULT_TEMPERATURE, DEFAULT_RETRIES, DEFAULT_TIMEOUT


class AgentExecutionError(Exception):
    """Raised when agent execution fails after all retries."""
    pass


def _resolve_output_type(output_type: Type[OutputT]) -> tuple[bool, Type]:
    """
    Determine if output_type is str or BaseModel and validate.
    """
    # Check if it's str
    if output_type is str:
        return False, str

    # Check if it's a BaseModel subclass
    try:
        if isinstance(output_type, type) and issubclass(output_type, BaseModel):
            return True, output_type
    except TypeError:
        pass

    # If we got here, it's an invalid type
    raise ValueError(
        f"output_type must be str or a Pydantic BaseModel subclass, got {output_type}"
    )


def create_agent(
    model: str,
    output_type: Type[OutputT],
    system_prompt: str,
    temperature: float = DEFAULT_TEMPERATURE,
    retries: int = DEFAULT_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
) -> Agent[None, OutputT]:
    """
    Create a Pydantic AI agent with standardized configuration.
    """
    # Validate output type
    is_structured, resolved_type = _resolve_output_type(output_type)

    # Create agent with appropriate configuration
    agent = Agent(
        model=model,
        result_type=resolved_type,
        system_prompt=system_prompt,
        retries=retries,
        model_settings={
            'temperature': temperature,
            'timeout': timeout,
        }
    )

    logfire.info(
        "Agent created",
        model=model,
        output_type=resolved_type.__name__,
        is_structured=is_structured,
        temperature=temperature,
        retries=retries,
        timeout=timeout
    )

    return agent


async def run_agent(
    prompt: str,
    output_type: Type[OutputT],
    system_prompt: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    retries: int = DEFAULT_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
) -> AgentResult[OutputT]:
    """
    One-shot agent creation and execution.

    Combines create_agent() + agent.run() for simple use cases.
    Returns wrapped result with metadata.
    """
    # Create agent
    agent = create_agent(
        model=model,
        output_type=output_type,
        system_prompt=system_prompt,
        temperature=temperature,
        retries=retries,
        timeout=timeout
    )

    # Execute with timing
    start_time = time.time()

    try:
        with logfire.span("agent.run", prompt_preview=prompt[:100]):
            result = await agent.run(prompt)

            latency_ms = (time.time() - start_time) * 1000

            # Extract usage metadata if available
            usage = {}
            if hasattr(result, '_result') and hasattr(result._result, 'usage'):
                usage_obj = result._result.usage
                if usage_obj:
                    usage = {
                        'prompt_tokens': getattr(usage_obj, 'request_tokens', 0),
                        'completion_tokens': getattr(usage_obj, 'response_tokens', 0),
                        'total_tokens': getattr(usage_obj, 'total_tokens', 0),
                    }
                    # Estimate cost (rough approximation, adjust per model)
                    if 'claude' in model.lower():
                        # Claude 3.5 Sonnet pricing: $3/$15 per 1M tokens
                        usage['total_cost'] = (
                            usage['prompt_tokens'] * 3 / 1_000_000 +
                            usage['completion_tokens'] * 15 / 1_000_000
                        )
                    elif 'gpt-4o' in model.lower():
                        # GPT-4o pricing: $2.50/$10 per 1M tokens
                        usage['total_cost'] = (
                            usage['prompt_tokens'] * 2.5 / 1_000_000 +
                            usage['completion_tokens'] * 10 / 1_000_000
                        )
                    else:
                        usage['total_cost'] = 0.0  # Unknown model pricing

            logfire.info(
                "Agent execution completed",
                latency_ms=latency_ms,
                usage=usage
            )

            return AgentResult(
                output=result.data,
                usage=usage,
                latency_ms=latency_ms
            )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logfire.error(
            "Agent execution failed",
            error=str(e),
            latency_ms=latency_ms
        )
        raise AgentExecutionError(f"Agent failed after retries: {e}") from e


async def run_agent_safe(
    agent: Agent,
    prompt: str,
    fallback_value: OutputT | None = None
) -> OutputT:
    """
    Run agent with error handling and optional fallback.

    Args:
        agent: Configured Pydantic AI agent
        prompt: User prompt to send to the agent
        fallback_value: Optional fallback value if execution fails

    Returns:
        Agent output or fallback value

    Raises:
        AgentExecutionError: If all retries fail and no fallback provided
    """
    try:
        result = await agent.run(prompt)
        return result.data
    except Exception as e:
        if fallback_value is not None:
            logfire.warn(f"Agent execution failed, using fallback: {e}")
            return fallback_value
        else:
            logfire.error(f"Agent execution failed: {e}")
            raise AgentExecutionError(f"Agent failed after retries: {e}") from e
