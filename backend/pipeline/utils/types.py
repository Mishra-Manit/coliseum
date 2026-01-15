"""Type definitions for Pydantic AI agent utilities."""

from typing import TypeVar, Generic, Union, Any
from pydantic import BaseModel, Field


# Generic type for agent output (str or Pydantic BaseModel)
OutputT = TypeVar('OutputT', bound=Union[str, BaseModel])


class AgentConfig(BaseModel):
    """Configuration for Pydantic AI agent creation.

    Attributes:
        model: Model identifier (e.g., "anthropic:claude-3-5-sonnet-20241022")
        temperature: Sampling temperature (0.0-1.0)
        retries: Number of retry attempts on failure
        timeout: Request timeout in seconds
    """
    model: str
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    retries: int = Field(default=2, ge=0)
    timeout: float = Field(default=30.0, gt=0.0)


class AgentResult(BaseModel, Generic[OutputT]):
    """Wrapper for agent execution results with metadata.

    Attributes:
        output: The validated model instance or string
        usage: Token usage statistics (prompt_tokens, completion_tokens, total_cost)
        latency_ms: Execution time in milliseconds
    """
    output: Any  # Will be OutputT but Pydantic doesn't support TypeVar in model fields directly
    usage: dict[str, Any] = Field(
        default_factory=dict,
        description="Token usage and cost statistics"
    )
    latency_ms: float = Field(
        default=0.0,
        description="Execution latency in milliseconds"
    )

    class Config:
        arbitrary_types_allowed = True
