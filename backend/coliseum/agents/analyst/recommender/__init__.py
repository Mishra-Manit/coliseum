"""Recommender Agent: Trade decision making based on research."""

from coliseum.agents.analyst.recommender.main import run_recommender
from coliseum.agents.analyst.recommender.models import (
    RecommenderDependencies,
    RecommenderOutput,
)

__all__ = [
    "run_recommender",
    "RecommenderDependencies",
    "RecommenderOutput",
]
