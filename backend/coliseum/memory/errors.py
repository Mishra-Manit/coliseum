"""Error history: structured JSONL log of every error with resolution status."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from coliseum.storage.state import get_data_dir

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
    errors_path = _get_errors_path()
    errors_path.parent.mkdir(parents=True, exist_ok=True)
    line = entry.model_dump_json() + "\n"

    try:
        with open(errors_path, "a", encoding="utf-8") as f:
            f.write(line)
        logger.info(
            "Logged error: component=%s error=%s resolution=%s",
            entry.component,
            entry.error,
            entry.resolution,
        )
    except Exception as e:
        logger.error("Failed to log error entry: %s", e)


def load_recent_errors(hours: int = 24) -> list[ErrorEntry]:
    """Load error entries from the last N hours."""
    errors_path = _get_errors_path()
    if not errors_path.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries: list[ErrorEntry] = []

    try:
        with open(errors_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = ErrorEntry(**data)
                    if entry.ts >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning("Skipping malformed error line: %s", e)
    except Exception as e:
        logger.error("Failed to load errors: %s", e)

    return entries


def detect_recurring_error(hours: int = 1, threshold: int = 3) -> tuple[bool, str]:
    """Return (True, description) if any error signature recurs >= threshold times in the last N hours. Groups similar errors."""
    from collections import Counter

    recent = load_recent_errors(hours=hours)
    if not recent:
        return False, ""

    counts: Counter[str] = Counter(e.error[:120] for e in recent)
    top_sig, top_count = counts.most_common(1)[0]
    if top_count >= threshold:
        return True, f"{top_sig!r} seen {top_count}x in the last {hours}h"

    return False, ""
