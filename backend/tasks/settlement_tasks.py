"""Settlement-related Celery tasks."""

import logging

from celery_config import celery_app
from database.session import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.check_settlements", queue="settlements")
def check_settlements():
    """
    Scheduled: Every 5 minutes

    Checks for closed events that need settlement.
    """
    import asyncio
    from services.settlement_service import settlement_service

    async def _check():
        async with get_db_session() as db:
            events = await settlement_service.check_for_settlements(db)

            # Spawn settlement task for each event
            for event in events:
                settle_event.delay(str(event.id))

            return {
                "events_to_settle": len(events),
                "event_ids": [str(e.id) for e in events],
            }

    return asyncio.run(_check())


@celery_app.task(
    name="tasks.settle_event",
    queue="settlements",
    bind=True,
    max_retries=5,
    default_retry_delay=300,  # 5 minutes
)
def settle_event(self, event_id: str):
    """
    Processes settlement for a single event.
    Validates outcome and updates all model balances.
    """
    import asyncio
    from uuid import UUID
    from services.settlement_service import settlement_service
    from services.websocket_service import websocket_service

    async def _settle():
        async with get_db_session() as db:
            try:
                settlement = await settlement_service.settle_event(db, UUID(event_id))

                # Get settlement results for broadcast
                results = await settlement_service.get_model_settlement_results(
                    db, UUID(event_id)
                )

                # Broadcast settlement
                await websocket_service.broadcast_settlement(
                    event_id=UUID(event_id),
                    settlement_data={
                        "outcome": settlement.outcome,
                        "results": [
                            {
                                "model_id": str(r["model_id"]),
                                "model_name": r["model_name"],
                                "position": r["position"],
                                "pnl": float(r["pnl"]),
                                "new_balance": float(r["new_balance"]),
                            }
                            for r in results
                        ],
                        "timestamp": settlement.settled_at.isoformat(),
                    },
                )

                return {
                    "event_id": event_id,
                    "outcome": settlement.outcome,
                    "total_bets_settled": settlement.total_bets_settled,
                    "total_pnl_distributed": float(settlement.total_pnl_distributed),
                }

            except ValueError as e:
                # Non-retryable error (already settled, not ready, etc.)
                logger.warning(f"Settlement skipped for {event_id}: {e}")
                return {"event_id": event_id, "skipped": True, "reason": str(e)}
            except Exception as e:
                logger.error(f"Settlement failed for {event_id}: {e}")
                raise self.retry(exc=e)

    return asyncio.run(_settle())
