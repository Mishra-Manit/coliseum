"""Data models for the Guardian agent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReconciliationStats(BaseModel):
    """Reconciliation summary stats for a Guardian run."""

    entries_inspected: int = 0
    kept_open: int = 0
    newly_closed: int = 0
    warnings: int = 0


class GuardianResult(BaseModel):
    """Result of a Guardian run."""

    positions_synced: int = 0
    reconciliation: ReconciliationStats = Field(default_factory=ReconciliationStats)
    warnings: list[str] = Field(default_factory=list)
    agent_summary: str = ""
