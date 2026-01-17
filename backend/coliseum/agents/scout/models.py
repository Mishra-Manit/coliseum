"""Data models for the Scout agent."""

from pydantic import BaseModel, Field
from coliseum.services.kalshi.client import KalshiClient
from coliseum.config import ScoutConfig
from coliseum.storage.files import OpportunitySignal

class ScoutDependencies(BaseModel):
    """Dependencies injected into Scout agent."""

    model_config = {"arbitrary_types_allowed": True}

    kalshi_client: KalshiClient
    config: ScoutConfig


class ScoutOutput(BaseModel):
    """Structured output from Scout agent scan."""

    opportunities: list[OpportunitySignal] = Field(
        description="List of high-quality trading opportunities discovered during scan. Each must have all required OpportunitySignal fields."
    )
    scan_summary: str = Field(
        description="Brief 2-3 sentence summary covering: categories found, quality assessment, notable filters applied"
    )
    markets_scanned: int = Field(
        description="Total number of markets returned by fetch_markets_closing_soon tool (before Scout filtering)"
    )
    opportunities_found: int = Field(
        description="Number of opportunities selected by Scout (length of opportunities list)"
    )
    filtered_out: int = Field(
        description="Markets rejected by Scout. Calculate as: markets_scanned - opportunities_found"
    )
