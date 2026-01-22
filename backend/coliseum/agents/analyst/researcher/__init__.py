"""Researcher Agent: Deep research and synthesis."""

from coliseum.agents.analyst.researcher.main import run_researcher
from coliseum.agents.analyst.researcher.models import (
    ResearcherDependencies,
    ResearcherOutput,
)

__all__ = [
    "run_researcher",
    "ResearcherDependencies",
    "ResearcherOutput",
]
