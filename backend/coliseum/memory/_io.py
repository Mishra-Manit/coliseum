"""Shared I/O primitives for JSONL operations."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def append_jsonl(path: Path, model: BaseModel) -> None:
    """Serialize a Pydantic model and append it as one JSONL line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = model.model_dump_json() + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def load_recent_jsonl(
    path: Path,
    model_cls: type[T],
    hours: int = 24,
    ts_field: str = "ts",
) -> list[T]:
    """Load JSONL entries whose timestamp field falls within the last *hours*."""
    if not path.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries: list[T] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = model_cls(**data)
                    if getattr(entry, ts_field) >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning("Skipping malformed JSONL line in %s: %s", path.name, e)
    except Exception as e:
        logger.error("Failed to load %s: %s", path, e)

    return entries
