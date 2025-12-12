"""Event-related Celery tasks."""

import logging
from datetime import date

from celery_config import celery_app
from database.session import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.select_daily_events", queue="events")
def select_daily_events(count: int = 5, selection_date: str = None):
    """
    Scheduled: Daily at 00:00 UTC

    Selects events from Kalshi that close today.
    Creates event records and triggers summary generation.
    """
    import asyncio
    from services.event_service import event_service

    async def _select():
        async with get_db_session() as db:
            target_date = date.fromisoformat(selection_date) if selection_date else None
            events = await event_service.select_daily_events(
                db, count=count, selection_date=target_date
            )

            # Trigger summary generation for each event
            for event in events:
                generate_event_summary.delay(str(event.id))

            return {
                "events_selected": len(events),
                "event_ids": [str(e.id) for e in events],
            }

    return asyncio.run(_select())


@celery_app.task(name="tasks.activate_event", queue="events")
def activate_event(event_id: str):
    """
    Triggered after summary is ready.

    Activates event and triggers betting sessions for all models.
    """
    import asyncio
    from uuid import UUID
    from services.event_service import event_service

    async def _activate():
        async with get_db_session() as db:
            event = await event_service.activate_event(db, UUID(event_id))

            # Trigger betting sessions
            launch_betting_sessions.delay(event_id)

            return {
                "event_id": str(event.id),
                "status": event.status,
                "title": event.title,
            }

    return asyncio.run(_activate())


@celery_app.task(name="tasks.check_and_close_events", queue="events")
def check_and_close_events():
    """
    Scheduled: Every minute

    Check for events past close time and close them.
    """
    import asyncio
    from services.event_service import event_service

    async def _check():
        async with get_db_session() as db:
            closed = await event_service.check_and_close_expired_events(db)
            return {
                "events_closed": len(closed),
                "event_ids": [str(e.id) for e in closed],
            }

    return asyncio.run(_check())


@celery_app.task(
    name="tasks.generate_event_summary",
    queue="ai",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def generate_event_summary(self, event_id: str):
    """
    Generates comprehensive event summary using AI with web search.
    Retries up to 3 times with exponential backoff.
    """
    import asyncio
    from uuid import UUID
    from services.summary_service import summary_service

    async def _generate():
        async with get_db_session() as db:
            try:
                summary = await summary_service.generate_event_summary(
                    db, UUID(event_id)
                )

                # Trigger event activation after summary is ready
                activate_event.delay(event_id)

                return {
                    "event_id": event_id,
                    "summary_id": str(summary.id),
                    "generation_time_ms": summary.generation_time_ms,
                }
            except Exception as e:
                logger.error(f"Summary generation failed: {e}")
                raise self.retry(exc=e)

    return asyncio.run(_generate())


@celery_app.task(name="tasks.launch_betting_sessions", queue="events")
def launch_betting_sessions(event_id: str):
    """
    Launches betting sessions for all 8 AI models.
    Spawns individual session tasks for parallel execution.
    """
    import asyncio
    from uuid import UUID
    from services.ai_model_service import ai_model_service
    from services.betting_session_service import betting_session_service

    async def _launch():
        async with get_db_session() as db:
            # Get all active models
            models = await ai_model_service.get_all_active_models(db)

            sessions = []
            for model in models:
                # Create session
                session = await betting_session_service.create_session(
                    db, UUID(event_id), model.id
                )
                sessions.append(session)

                # Spawn task for each session
                run_betting_session.delay(str(session.id))

            return {
                "event_id": event_id,
                "sessions_launched": len(sessions),
                "session_ids": [str(s.id) for s in sessions],
            }

    return asyncio.run(_launch())


@celery_app.task(
    name="tasks.run_betting_session",
    queue="ai",
    bind=True,
    time_limit=300,  # 5 minute timeout
    soft_time_limit=240,
)
def run_betting_session(self, session_id: str):
    """
    Executes a single AI model betting session.

    - Generates reasoning messages
    - Makes betting decision
    - Places bet if applicable
    """
    import asyncio
    from uuid import UUID
    from services.betting_session_service import betting_session_service
    from services.websocket_service import websocket_service

    async def _run():
        async with get_db_session() as db:
            # Define broadcast callback
            async def broadcast_message(message):
                session = await betting_session_service.get_session(db, UUID(session_id))
                if session:
                    await websocket_service.broadcast_message(
                        event_id=session.event_id,
                        session_id=session.id,
                        message_data={
                            "id": str(message.id),
                            "model_id": str(session.model_id),
                            "content": message.content,
                            "message_type": message.message_type,
                            "action": {
                                "type": message.action_type,
                                "amount": float(message.action_amount) if message.action_amount else None,
                                "shares": message.action_shares,
                                "price": float(message.action_price) if message.action_price else None,
                            } if message.action_type else None,
                            "timestamp": message.created_at.isoformat(),
                        },
                    )

            session = await betting_session_service.run_session(
                db, UUID(session_id), broadcast_callback=broadcast_message
            )

            return {
                "session_id": str(session.id),
                "status": session.status,
                "final_position": session.final_position,
                "confidence": float(session.confidence_score) if session.confidence_score else None,
            }

    return asyncio.run(_run())
