"""Maintenance Celery tasks."""

import logging
from datetime import date, datetime, timedelta, timezone

from celery_config import celery_app
from database.session import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.update_leaderboard", queue="maintenance")
def update_leaderboard():
    """
    Scheduled: Hourly

    Calculates and caches leaderboard rankings.
    Updates daily_leaderboards table.
    """
    import asyncio
    from services.leaderboard_service import leaderboard_service

    async def _update():
        async with get_db_session() as db:
            snapshots = await leaderboard_service.update_daily_snapshot(db)
            return {
                "snapshots_updated": len(snapshots),
                "date": date.today().isoformat(),
            }

    return asyncio.run(_update())


@celery_app.task(name="tasks.simulate_viewers", queue="maintenance")
def simulate_viewers():
    """
    Scheduled: Every 10 seconds

    Updates simulated viewer counts based on activity.
    """
    import asyncio
    import random
    from services.event_service import event_service
    from services.websocket_service import websocket_service

    async def _simulate():
        async with get_db_session() as db:
            events = await event_service.get_active_events(db)

            updated = []
            for event in events:
                # Generate viewer count based on subscribers + random
                base_count = websocket_service.get_viewer_count(event.id)
                # Add some randomness for realism
                variation = random.randint(-50, 100)
                new_count = max(100, base_count + variation)

                # Update in database
                await event_service.update_viewer_count(db, event.id, new_count)

                # Broadcast
                await websocket_service.broadcast_viewer_count(event.id, new_count)

                updated.append({
                    "event_id": str(event.id),
                    "viewers": new_count,
                })

            return {
                "events_updated": len(updated),
                "updates": updated,
            }

    return asyncio.run(_simulate())


@celery_app.task(name="tasks.cleanup_old_data", queue="maintenance")
def cleanup_old_data():
    """
    Scheduled: Daily at 03:00 UTC

    Archives old sessions, compresses price history.
    """
    import asyncio
    from sqlalchemy import delete
    from models import PriceHistory, SessionMessage

    async def _cleanup():
        async with get_db_session() as db:
            # Delete price history older than 30 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            result = await db.execute(
                delete(PriceHistory).where(PriceHistory.recorded_at < cutoff)
            )
            price_records_deleted = result.rowcount

            # Delete session messages older than 7 days (keep summaries in sessions)
            message_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

            result = await db.execute(
                delete(SessionMessage).where(SessionMessage.created_at < message_cutoff)
            )
            messages_deleted = result.rowcount

            await db.commit()

            return {
                "price_records_deleted": price_records_deleted,
                "session_messages_deleted": messages_deleted,
                "cutoff_date": cutoff.isoformat(),
            }

    return asyncio.run(_cleanup())


@celery_app.task(name="tasks.initialize_models", queue="maintenance")
def initialize_models():
    """
    Initialize or update all AI models in the database.
    Run this on startup or when model config changes.
    """
    import asyncio
    from services.ai_model_service import ai_model_service

    async def _init():
        async with get_db_session() as db:
            models = await ai_model_service.initialize_models(db)
            return {
                "models_initialized": len(models),
                "model_ids": [str(m.id) for m in models],
            }

    return asyncio.run(_init())
