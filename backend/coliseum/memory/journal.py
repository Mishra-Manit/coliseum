"""Run journal: append-only daily markdown files recording each pipeline cycle."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from coliseum.storage._io import atomic_write
from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)


class JournalCycleSummary(BaseModel):
    """Summary of a single pipeline cycle for journal entry."""

    cycle_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0
    guardian_summary: str = ""
    scout_summary: str = ""
    analyst_summary: str = ""
    trader_summary: str = ""
    portfolio_cash: float = 0.0
    portfolio_positions_value: float = 0.0
    portfolio_total: float = 0.0
    open_position_count: int = 0
    errors: list[str] = Field(default_factory=list)


def _get_journal_dir() -> Path:
    """Get the journal directory, creating it if needed."""
    journal_dir = get_data_dir() / "memory" / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    return journal_dir


def _format_journal_entry(summary: JournalCycleSummary) -> str:
    """Format a cycle summary as a markdown journal entry."""
    ts = summary.cycle_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    if summary.errors:
        errors_line = ", ".join(summary.errors)
    else:
        errors_line = "None"

    return f"""## Cycle {ts}

- **Duration**: {summary.duration_seconds:.0f}s
- **Guardian**: {summary.guardian_summary or "N/A"}
- **Scout**: {summary.scout_summary or "N/A"}
- **Analyst**: {summary.analyst_summary or "N/A"}
- **Trader**: {summary.trader_summary or "N/A"}
- **Portfolio**: Cash ${summary.portfolio_cash:.2f} | Positions ${summary.portfolio_positions_value:.2f} | Total ${summary.portfolio_total:.2f}
- **Open Positions**: {summary.open_position_count}
- **Errors**: {errors_line}

"""


def write_journal_entry(summary: JournalCycleSummary) -> Path:
    """Append a cycle summary to today's journal file."""
    journal_dir = _get_journal_dir()
    date_str = summary.cycle_timestamp.strftime("%Y-%m-%d")
    journal_path = journal_dir / f"{date_str}.md"

    entry_text = _format_journal_entry(summary)

    if journal_path.exists():
        existing = journal_path.read_text(encoding="utf-8")
        new_content = existing + entry_text
    else:
        new_content = f"# Run Journal — {date_str}\n\n{entry_text}"

    atomic_write(journal_path, new_content)
    logger.info("Wrote journal entry to %s", journal_path)
    return journal_path


def load_recent_journal(days: int = 2) -> str:
    """Load journal entries from the last N days as a single string."""
    journal_dir = _get_journal_dir()
    now = datetime.now(timezone.utc)
    parts: list[str] = []

    for offset in range(days):
        date = now - timedelta(days=offset)
        date_str = date.strftime("%Y-%m-%d")
        journal_path = journal_dir / f"{date_str}.md"
        if journal_path.exists():
            try:
                parts.append(journal_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to read journal %s: %s", journal_path, e)

    if parts:
        return "\n".join(parts)
    else:
        return "(No recent journal entries)"
