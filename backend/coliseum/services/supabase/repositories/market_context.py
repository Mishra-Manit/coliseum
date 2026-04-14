"""DB repository for market category context persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from coliseum.services.supabase.db import get_db_session
from coliseum.services.supabase.models import MarketCategoryContext

logger = logging.getLogger(__name__)


async def load_category_context(category_key: str) -> MarketCategoryContext | None:
    """Load a single category's context row. Returns None if not found."""
    async with get_db_session() as session:
        result = await session.execute(
            select(MarketCategoryContext).where(
                MarketCategoryContext.category_key == category_key
            )
        )
        return result.scalar_one_or_none()


async def upsert_category_context(
    category_key: str,
    label: str,
    resolution_desc_template: str,
    uses_slug: bool,
    resolution_rules: str,
    known_disputes: str,
    edge_cases: str,
    risk_questions: list[str],
    sources: list[str],
    refresh_duration_seconds: int | None,
) -> None:
    """Insert or update a category context row."""
    now = datetime.now(timezone.utc)
    values = {
        "category_key": category_key,
        "label": label,
        "resolution_desc_template": resolution_desc_template,
        "uses_slug": uses_slug,
        "resolution_rules": resolution_rules,
        "known_disputes": known_disputes,
        "edge_cases": edge_cases,
        "risk_questions": risk_questions,
        "sources": sources,
        "last_refreshed_at": now,
        "refresh_duration_seconds": refresh_duration_seconds,
    }
    async with get_db_session() as session:
        stmt = pg_insert(MarketCategoryContext).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["category_key"],
            set_={
                "label": stmt.excluded.label,
                "resolution_desc_template": stmt.excluded.resolution_desc_template,
                "uses_slug": stmt.excluded.uses_slug,
                "resolution_rules": stmt.excluded.resolution_rules,
                "known_disputes": stmt.excluded.known_disputes,
                "edge_cases": stmt.excluded.edge_cases,
                "risk_questions": stmt.excluded.risk_questions,
                "sources": stmt.excluded.sources,
                "last_refreshed_at": stmt.excluded.last_refreshed_at,
                "refresh_duration_seconds": stmt.excluded.refresh_duration_seconds,
            },
        )
        await session.execute(stmt)
        await session.commit()
