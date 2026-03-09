"""Decision log: structured append-only JSONL of every BUY/SKIP decision with reasoning."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field

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
    execution_status: str = ""
    outcome: str | None = None


def _get_decisions_path() -> Path:
    """Get the decisions JSONL file path."""
    return get_data_dir() / "memory" / "decisions.jsonl"


def log_decision(entry: DecisionEntry) -> None:
    """Append a decision entry to the JSONL log."""
    decisions_path = _get_decisions_path()
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    line = entry.model_dump_json() + "\n"

    try:
        with open(decisions_path, "a", encoding="utf-8") as f:
            f.write(line)
        logger.info("Logged decision: %s %s %s", entry.action, entry.ticker, entry.execution_status)
    except Exception as e:
        logger.error("Failed to log decision for %s: %s", entry.ticker, e)


def load_recent_decisions(hours: int = 24) -> list[DecisionEntry]:
    """Load decision entries from the last N hours."""
    decisions_path = _get_decisions_path()
    if not decisions_path.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries: list[DecisionEntry] = []

    try:
        with open(decisions_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = DecisionEntry(**data)
                    if entry.ts >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning("Skipping malformed decision line: %s", e)
    except Exception as e:
        logger.error("Failed to load decisions: %s", e)

    return entries
