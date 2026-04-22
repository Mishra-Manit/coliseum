"""Run journal: Pydantic model for pipeline cycle summaries."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class JournalCycleSummary(BaseModel):
    """Summary of a single pipeline cycle for journal entry."""

    cycle_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0
    scout_summary: str = ""
    analyst_summary: str = ""
    trader_summary: str = ""
    portfolio_cash: float = 0.0
    portfolio_positions_value: float = 0.0
    portfolio_total: float = 0.0
    open_position_count: int = 0
    errors: list[str] = Field(default_factory=list)
