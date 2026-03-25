"""Pydantic models for Analyst sub-agents (Researcher + Recommender)."""

from pydantic import BaseModel


class AnalystDependencies(BaseModel):
    """Shared dependencies injected into both Researcher and Recommender agents."""
    opportunity_id: str


class ResearcherOutput(BaseModel):
    """Output from Researcher agent run."""
    synthesis: str  # Markdown synthesis with Sources section at bottom


class RecommenderOutput(BaseModel):
    """Output from Recommender agent run."""

    reasoning: str  # ~100 words, concise evaluation reasoning
