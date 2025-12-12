"""Price update Celery tasks."""

import logging

from celery_config import celery_app
from database.session import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.update_prices", queue="prices")
def update_prices():
    """
    Scheduled: Every 30 seconds

    Fetches latest prices from Kalshi for all active events.
    Broadcasts updates via WebSocket.
    """
    import asyncio
    from services.event_service import event_service
    from services.kalshi_service import kalshi_service
    from services.websocket_service import websocket_service

    async def _update():
        async with get_db_session() as db:
            # Get active events
            events = await event_service.get_active_events(db)

            updated = []
            for event in events:
                if event.kalshi_market_id:
                    price = await kalshi_service.get_market_price(
                        event.kalshi_market_id
                    )
                    if price is not None and price != event.current_price:
                        # Update in database
                        await event_service.update_event_price(db, event.id, price)

                        # Broadcast via WebSocket
                        await websocket_service.broadcast_price_update(
                            event.id, price
                        )

                        updated.append({
                            "event_id": str(event.id),
                            "old_price": float(event.current_price),
                            "new_price": float(price),
                        })

            return {
                "events_checked": len(events),
                "events_updated": len(updated),
                "updates": updated,
            }

    return asyncio.run(_update())


@celery_app.task(name="tasks.record_price_history", queue="prices")
def record_price_history():
    """
    Scheduled: Every 5 minutes

    Records current prices to price_history table.
    """
    import asyncio
    from models import PriceHistory
    from services.event_service import event_service

    async def _record():
        async with get_db_session() as db:
            events = await event_service.get_active_events(db)

            recorded = 0
            for event in events:
                price_record = PriceHistory(
                    event_id=event.id,
                    price=event.current_price,
                    source="kalshi",
                )
                db.add(price_record)
                recorded += 1

            await db.commit()

            return {
                "prices_recorded": recorded,
            }

    return asyncio.run(_record())
