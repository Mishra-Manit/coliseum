"""Data models for the Guardian agent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from coliseum.config import Settings
from coliseum.services.kalshi.client import KalshiClient
from coliseum.storage.state import PortfolioState


class GuardianDependencies(BaseModel):
    """Dependencies injected into Guardian agent."""

    model_config = {"arbitrary_types_allowed": True}

    kalshi_client: KalshiClient
    settings: Settings
    synced_state: PortfolioState | None = None
    fills: list[dict[str, Any]] | None = None
    reconciliation: ReconciliationStats | None = None


class ReconciliationStats(BaseModel):
    """Reconciliation summary stats for a Guardian run."""

    entries_inspected: int = 0
    kept_open: int = 0
    newly_closed: int = 0
    skipped_no_trade: int = 0
    warnings: int = 0


class GuardianResult(BaseModel):
    """Result of a Guardian run."""

    positions_synced: int = 0
    reconciliation: ReconciliationStats = Field(default_factory=ReconciliationStats)
    warnings: list[str] = Field(default_factory=list)
    agent_summary: str = Field(
        default="",
        description="Brief summary of Guardian sync/reconciliation actions.",
    )
