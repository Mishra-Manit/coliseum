"""Pydantic models for Analyst sub-agents (Researcher + Recommender)."""

from pydantic import BaseModel

from coliseum.config import AnalystConfig


class AnalystDependencies(BaseModel):
    """Shared dependencies injected into both Researcher and Recommender agents."""
    opportunity_id: str
    config: AnalystConfig


class ResearcherOutput(BaseModel):
    """Output from Researcher agent run."""
    synthesis: str  # Markdown synthesis with Sources section at bottom


class RecommenderOutput(BaseModel):
    """Output from Recommender agent run."""

    # Trade evaluation metrics (YES-side)
    estimated_true_probability: float  # 0.0 to 1.0 (p_yes)
    current_market_price: float  # 0.0 to 1.0 (yes_price)
    expected_value: float  # ev_yes
    edge: float  # edge_yes
    suggested_position_pct: float  # 0.0 to 0.10 (size_yes)
    reasoning: str  # ~100 words, concise evaluation reasoning

    # NO-side metrics (derived from p_no = 1 - p_yes, calculated after agent output)
    edge_no: float = 0.0  # p_no - no_price
    expected_value_no: float = 0.0  # EV for NO side
    suggested_position_pct_no: float = 0.0  # Kelly sizing for NO side
