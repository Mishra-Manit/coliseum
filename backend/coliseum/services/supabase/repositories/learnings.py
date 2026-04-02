"""DB repository for system learnings persistence."""

from __future__ import annotations

import logging
from collections import defaultdict

import logfire
from sqlalchemy import select, update

from coliseum.memory.enums import LearningAddition
from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import Learning

logger = logging.getLogger(__name__)


async def load_learnings_from_db(section: str | None = None) -> str:
    """Load active learnings from the database, formatted as markdown with row IDs."""
    query = select(Learning).where(Learning.active.is_(True)).order_by(
        Learning.category, Learning.created_at
    )

    if section is not None:
        query = query.where(Learning.category == section)

    async with get_db_session() as session:
        result = await session.execute(query)
        rows = result.scalars().all()

    if not rows:
        return "(No learnings recorded yet)"

    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[row.category].append(f"[#{row.id}] {row.content}")

    sections: list[str] = ["# System Learnings"]
    for category, entries in grouped.items():
        sections.append(f"\n## {category}")
        sections.append("\n".join(entries))

    return "\n".join(sections)


async def apply_scribe_operations(
    deletions: list[int],
    additions: list[LearningAddition],
) -> None:
    """Apply Scribe operations atomically: soft-delete then insert in one transaction."""
    if not deletions and not additions:
        return

    async with get_db_session() as session:
        if deletions:
            result = await session.execute(
                update(Learning)
                .where(Learning.id.in_(deletions), Learning.active.is_(True))
                .values(active=False)
            )
            affected = result.rowcount
            if affected < len(deletions):
                logfire.warn(
                    "Scribe soft-delete mismatch: requested %d, affected %d",
                    len(deletions),
                    affected,
                )

        if additions:
            rows = [
                Learning(category=str(a.category), content=a.content)
                for a in additions
            ]
            session.add_all(rows)

        await session.commit()

    logger.info(
        "Applied scribe operations: %d deletions, %d additions",
        len(deletions),
        len(additions),
    )
