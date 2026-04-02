"""Enums and shared models for the memory system."""

from enum import StrEnum

from pydantic import BaseModel


class LearningCategory(StrEnum):
    """Valid categories for system learnings."""

    MARKET_PATTERNS = "Market Patterns"
    EXECUTION_PATTERNS = "Execution Patterns"
    ERROR_PATTERNS = "Error Patterns"


class LearningAddition(BaseModel):
    """A new learning to add to the knowledge base."""

    category: LearningCategory
    content: str
