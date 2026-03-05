"""Learnings store: long-lived markdown file with accumulated system-level insights."""

import logging
from pathlib import Path

from coliseum.storage.state import get_data_dir

logger = logging.getLogger(__name__)

LEARNINGS_SEED = """# System Learnings

## Market Patterns
- Sports markets resolve faster than political markets (avg 2h vs 12h post-event)
- Weather markets often have wide spreads even at high certainty — factor into scout filters

## Execution Patterns
- Orders placed within 2h of close fill faster
- Reprice aggression of 0.02 works well for >$5k volume markets, increase to 0.03 for thinner books

## Error Patterns
- Kalshi API may return 429 during maintenance windows — skip scout cycles then
- Exa search times out on queries >200 chars — keep research queries concise
"""


def _get_learnings_path() -> Path:
    """Get the learnings markdown file path, ensuring parent dir exists."""
    memory_dir = get_data_dir() / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir / "learnings.md"


def ensure_learnings_seed() -> Path:
    """Create the learnings file with seed content if it doesn't exist."""
    learnings_path = _get_learnings_path()
    if not learnings_path.exists():
        learnings_path.write_text(LEARNINGS_SEED, encoding="utf-8")
        logger.info("Created learnings seed at %s", learnings_path)
    return learnings_path


def load_learnings(section: str | None = None) -> str:
    """Load learnings content, optionally filtered to a specific section."""
    learnings_path = _get_learnings_path()

    if not learnings_path.exists():
        return "(No learnings recorded yet)"

    try:
        content = learnings_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Failed to read learnings: %s", e)
        return "(Error reading learnings)"

    if section is None:
        return content

    lines = content.split("\n")
    section_lines: list[str] = []
    in_section = False
    target = f"## {section}"

    for line in lines:
        if line.strip().startswith("## "):
            if line.strip().lower() == target.lower():
                in_section = True
                section_lines.append(line)
                continue
            elif in_section:
                break
        if in_section:
            section_lines.append(line)

    if not section_lines:
        return f"(No learnings found for section: {section})"

    return "\n".join(section_lines).strip()
