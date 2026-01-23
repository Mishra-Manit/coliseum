"""Pydantic models for Researcher agent."""

from pydantic import BaseModel

from coliseum.config import AnalystConfig
from coliseum.services.exa.client import ExaClient


class ResearcherDependencies(BaseModel):
    """Dependencies injected into Researcher agent context."""

    model_config = {"arbitrary_types_allowed": True}

    exa_client: ExaClient
    opportunity_id: str
    config: AnalystConfig


class ResearcherOutput(BaseModel):
    """Output from Researcher agent run."""

    synthesis: str
    sources: list[str]
    summary: str  # 1-2 sentence summary of research
    sources_count: int
