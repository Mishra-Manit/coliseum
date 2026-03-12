"""Data models for the Guardian agent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReconciliationStats(BaseModel):
    """Reconciliation summary stats for a Guardian run."""

    entries_inspected: int = 0
    kept_open: int = 0
    newly_closed: int = 0
    duplicate_close_skipped: int = 0
    stop_loss_exits: int = 0
    warnings: int = 0


class GuardianResult(BaseModel):
    """Result of a Guardian run."""

    positions_synced: int = 0
    reconciliation: ReconciliationStats = Field(default_factory=ReconciliationStats)
    stop_loss_tickers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    agent_summary: str = ""


class LearningReflectionOutput(BaseModel):
    """Structured output from the Scribe reflection agent."""

    updated_learnings_md: str
    summary: str
