"""Pydantic models for Recommender agent."""

from pydantic import BaseModel

from coliseum.config import AnalystConfig


class RecommenderDependencies(BaseModel):
    """Dependencies injected into Recommender agent context."""

    opportunity_id: str
    config: AnalystConfig


class RecommenderOutput(BaseModel):
    """Output from Recommender agent run."""

    # Trade evaluation metrics
    estimated_true_probability: float  # 0.0 to 1.0
    current_market_price: float  # 0.0 to 1.0
    expected_value: float
    edge: float
    suggested_position_pct: float  # 0.0 to 0.10
    reasoning: str  # 200-400 words
    decision_summary: str  # 1-2 sentence summary of evaluation
