"""Error history: structured JSONL log of every error with resolution status."""

import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from coliseum.config import get_data_dir
from coliseum.memory._io import append_jsonl, load_recent_jsonl

logger = logging.getLogger(__name__)


class ErrorEntry(BaseModel):
    """One error record."""

    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    component: str = ""
    error: str = ""
    resolution: str = ""
    attempts: int = 1
    details: str = ""


def _get_errors_path() -> Path:
    """Get the errors JSONL file path."""
    return get_data_dir() / "memory" / "errors.jsonl"


def log_error(entry: ErrorEntry) -> None:
    """Append an error entry to the JSONL log."""
    append_jsonl(_get_errors_path(), entry)
    logger.info(
        "Logged error: component=%s error=%s resolution=%s",
        entry.component,
        entry.error,
        entry.resolution,
    )


def load_recent_errors(hours: int = 24) -> list[ErrorEntry]:
    """Load error entries from the last N hours."""
    return load_recent_jsonl(_get_errors_path(), ErrorEntry, hours=hours)


def detect_recurring_error(hours: int = 1, threshold: int = 3) -> tuple[bool, str]:
    """Return (True, description) if any error signature recurs >= threshold times in the last N hours. Groups similar errors."""
    recent = load_recent_errors(hours=hours)
    if not recent:
        return False, ""

    counts: Counter[str] = Counter(e.error[:120] for e in recent)
    top_sig, top_count = counts.most_common(1)[0]
    if top_count >= threshold:
        return True, f"{top_sig!r} seen {top_count}x in the last {hours}h"

    return False, ""
