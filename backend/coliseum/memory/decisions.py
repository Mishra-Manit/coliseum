"""Decision log: structured append-only JSONL of every BUY/SKIP decision with reasoning."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from coliseum.storage._io import append_jsonl, load_recent_jsonl
from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)


class DecisionEntry(BaseModel):
    """One trading decision record."""

    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    opportunity_id: str = ""
    ticker: str = ""
    action: str = ""
    price: float | None = None
    contracts: int = 0
    confidence: float = 0.0
    reasoning: str = ""
    tldr: str = ""
    execution_status: str = ""
    outcome: str | None = None


def _get_decisions_path() -> Path:
    """Get the decisions JSONL file path."""
    return get_data_dir() / "memory" / "decisions.jsonl"


def log_decision(entry: DecisionEntry) -> None:
    """Append a decision entry to the JSONL log."""
    append_jsonl(_get_decisions_path(), entry)
    logger.info("Logged decision: %s %s %s", entry.action, entry.ticker, entry.execution_status)


def load_recent_decisions(hours: int = 24) -> list[DecisionEntry]:
    """Load decision entries from the last N hours."""
    return load_recent_jsonl(_get_decisions_path(), DecisionEntry, hours=hours)
