"""File-based job queue for inter-agent communication.

Implements a simple file-based queue system where Scout queues work for Analyst,
and Analyst queues work for Trader. Queue items are JSON files prefixed with a timestamp
to ensure natural chronological ordering.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)


class QueueItem(BaseModel):
    """Queue item metadata."""

    id: str
    opportunity_id: str | None = None
    recommendation_id: str | None = None
    queued_at: datetime
    file_path: Path


def _get_queue_dir(agent_name: Literal["analyst", "trader"]) -> Path:
    if agent_name not in {"analyst", "trader"}:
        raise ValueError(f"Invalid agent name: {agent_name}")

    queue_dir = get_data_dir() / "queue" / agent_name
    queue_dir.mkdir(parents=True, exist_ok=True)
    return queue_dir


def _generate_queue_filename() -> str:
    """Generate timestamp-prefixed filename (YYYYMMDD_HHMMSS_{uuid}.json)."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]
    return f"{timestamp}_{unique_id}.json"


def queue_for_analyst(opportunity_id: str) -> None:
    """Queue an opportunity ID for the Analyst agent.

    Note: Deduplication is handled upstream via is_market_seen() check.
    """
    queue_dir = _get_queue_dir("analyst")
    file_path = queue_dir / _generate_queue_filename()

    item = {
        "opportunity_id": opportunity_id,
        "queued_at": datetime.utcnow().isoformat(),
    }

    try:
        file_path.write_text(json.dumps(item, indent=2), encoding="utf-8")
        logger.info(f"Queued opportunity {opportunity_id} for Analyst")
    except Exception as e:
        logger.error(f"Failed to queue opportunity {opportunity_id}: {e}")
        raise


def queue_for_trader(recommendation_id: str) -> None:
    """Queue a recommendation ID for the Trader agent."""
    queue_dir = _get_queue_dir("trader")
    file_path = queue_dir / _generate_queue_filename()

    item = {
        "recommendation_id": recommendation_id,
        "queued_at": datetime.utcnow().isoformat(),
    }

    try:
        file_path.write_text(json.dumps(item, indent=2), encoding="utf-8")
        logger.info(f"Queued recommendation {recommendation_id} for Trader")
    except Exception as e:
        logger.error(f"Failed to queue recommendation {recommendation_id}: {e}")
        raise


def get_pending(agent_name: Literal["analyst", "trader"]) -> list[QueueItem]:
    """Get all pending queue items, sorted oldest first."""
    queue_dir = _get_queue_dir(agent_name)
    queue_files = sorted(queue_dir.glob("*.json"))

    items = []
    for file_path in queue_files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            items.append(QueueItem(
                id=file_path.stem,
                opportunity_id=data.get("opportunity_id"),
                recommendation_id=data.get("recommendation_id"),
                queued_at=datetime.fromisoformat(data["queued_at"]),
                file_path=file_path,
            ))
        except Exception as e:
            logger.warning(f"Failed to parse queue item {file_path}: {e}")
            continue

    logger.debug(f"Found {len(items)} pending items for {agent_name}")
    return items


def dequeue(agent_name: Literal["analyst", "trader"], item_id: str) -> None:
    """Remove a processed queue item cleanly (idempotent)."""
    queue_dir = _get_queue_dir(agent_name)
    file_path = queue_dir / f"{item_id}.json"

    try:
        file_path.unlink(missing_ok=True)
        logger.debug(f"Dequeued item {item_id} from {agent_name} queue")
    except Exception as e:
        logger.warning(f"Failed to dequeue item {item_id}: {e}")


def clear_queue(agent_name: Literal["analyst", "trader"]) -> int:
    """Clear all items from an agent's queue."""
    queue_dir = _get_queue_dir(agent_name)
    count = 0
    for file_path in list(queue_dir.glob("*.json")):
        try:
            file_path.unlink()
            count += 1
        except Exception as e:
            logger.warning(f"Failed to delete queue file {file_path}: {e}")

    logger.info(f"Cleared {count} items from {agent_name} queue")
    return count
