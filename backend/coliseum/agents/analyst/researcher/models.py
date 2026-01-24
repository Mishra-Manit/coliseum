"""Pydantic models for Researcher agent."""

from pydantic import BaseModel

from coliseum.config import AnalystConfig

class ResearcherDependencies(BaseModel):
    """Dependencies injected into Researcher agent context."""
    opportunity_id: str
    config: AnalystConfig


class ResearcherOutput(BaseModel):
    """Output from Researcher agent run."""
    synthesis: str  # Markdown synthesis with Sources section at bottom
