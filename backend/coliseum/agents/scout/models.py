"""Data models for the Scout agent."""

from pydantic import BaseModel
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

    opportunities: list[OpportunitySignal]
    scan_summary: str
    markets_scanned: int
    opportunities_found: int
    filtered_out: int
