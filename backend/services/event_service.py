"""Event management service."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Event, EventSummary
from services.kalshi_service import kalshi_service

logger = logging.getLogger(__name__)


class EventService:
    """
    Manages the lifecycle of prediction market events.
    Handles selection, activation, and status transitions.
    """

    async def select_daily_events(
        self,
        db: AsyncSession,
        count: int = 5,
        selection_date: Optional[date] = None,
    ) -> list[Event]:
        """
        Select events for today's competition.

        Criteria:
        - Closes within 24 hours
        - Has sufficient trading volume
        - Interesting category diversity
        - Not already selected
        """
        if selection_date is None:
            selection_date = date.today()

        # Fetch events from Kalshi
        kalshi_events = await kalshi_service.get_events_closing_today()

        if not kalshi_events:
            logger.warning("No events found closing today")
            return []

        # Filter out already selected events
        existing_ids = await self._get_existing_kalshi_ids(db)
        new_events = [
            e for e in kalshi_events
            if e.get("ticker") not in existing_ids
        ]

        # Sort by volume/interest and take top N
        new_events.sort(
            key=lambda x: x.get("volume", 0) + x.get("open_interest", 0),
            reverse=True,
        )

        selected = []
        for kalshi_event in new_events[:count]:
            event = await self._create_event_from_kalshi(
                db, kalshi_event, selection_date
            )
            if event:
                selected.append(event)

        await db.commit()
        logger.info(f"Selected {len(selected)} events for {selection_date}")
        return selected

    async def _get_existing_kalshi_ids(self, db: AsyncSession) -> set[str]:
        """Get set of already selected Kalshi market IDs."""
        result = await db.execute(
            select(Event.kalshi_market_id).where(Event.kalshi_market_id.isnot(None))
        )
        return {r[0] for r in result.all()}

    async def _create_event_from_kalshi(
        self,
        db: AsyncSession,
        kalshi_data: dict,
        selection_date: date,
    ) -> Optional[Event]:
        """Create an Event from Kalshi market data."""
        try:
            close_time_str = kalshi_data.get("close_time")
            close_time = datetime.fromisoformat(
                close_time_str.replace("Z", "+00:00")
            )

            # Get current price (Kalshi returns in cents)
            yes_price = kalshi_data.get("yes_bid", 50)
            current_price = Decimal(str(yes_price)) / 100

            event = Event(
                kalshi_event_id=kalshi_data.get("event_ticker"),
                kalshi_market_id=kalshi_data.get("ticker"),
                title=kalshi_data.get("title", "Unknown Event"),
                question=kalshi_data.get("title", "Unknown Event"),
                current_price=current_price,
                category=kalshi_data.get("category", "General"),
                subcategory=kalshi_data.get("subcategory"),
                tags=kalshi_data.get("tags", []),
                market_context=kalshi_data.get("subtitle", ""),
                status="pending",
                selection_date=selection_date,
                close_time=close_time,
                kalshi_data=kalshi_data,
            )
            db.add(event)
            return event

        except Exception as e:
            logger.error(f"Error creating event from Kalshi data: {e}")
            return None

    async def add_manual_event(
        self,
        db: AsyncSession,
        kalshi_market_id: str,
        selection_date: Optional[date] = None,
    ) -> Optional[Event]:
        """Manually add an event by Kalshi market ID."""
        if selection_date is None:
            selection_date = date.today()

        # Fetch market details
        market = await kalshi_service.get_market_details(kalshi_market_id)
        if not market:
            return None

        return await self._create_event_from_kalshi(db, market, selection_date)

    async def activate_event(self, db: AsyncSession, event_id: UUID) -> Event:
        """Transition event from pending to active state."""
        event = await self.get_event(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        if event.status != "pending":
            raise ValueError(f"Event {event_id} is not in pending status")

        event.status = "active"
        await db.commit()
        await db.refresh(event)
        logger.info(f"Activated event: {event.title}")
        return event

    async def close_event(self, db: AsyncSession, event_id: UUID) -> Event:
        """Mark event as closed when betting period ends."""
        event = await self.get_event(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        event.status = "closed"
        await db.commit()
        await db.refresh(event)
        logger.info(f"Closed event: {event.title}")
        return event

    async def settle_event(
        self,
        db: AsyncSession,
        event_id: UUID,
        outcome: str,
    ) -> Event:
        """Mark event as settled with outcome."""
        event = await self.get_event(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        event.status = "settled"
        event.outcome = outcome
        event.settlement_time = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(event)
        logger.info(f"Settled event: {event.title} with outcome {outcome}")
        return event

    async def get_event(self, db: AsyncSession, event_id: UUID) -> Optional[Event]:
        """Fetch single event by ID."""
        result = await db.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_event_with_summary(
        self, db: AsyncSession, event_id: UUID
    ) -> Optional[Event]:
        """Fetch event with its summary."""
        result = await db.execute(
            select(Event)
            .options(selectinload(Event.summary))
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_active_events(self, db: AsyncSession) -> list[Event]:
        """Fetch all currently active events."""
        result = await db.execute(
            select(Event)
            .where(Event.status == "active")
            .order_by(Event.close_time)
        )
        return list(result.scalars().all())

    async def get_pending_events(self, db: AsyncSession) -> list[Event]:
        """Fetch all pending events."""
        result = await db.execute(
            select(Event)
            .where(Event.status == "pending")
            .order_by(Event.close_time)
        )
        return list(result.scalars().all())

    async def get_closed_events(self, db: AsyncSession) -> list[Event]:
        """Fetch all closed (awaiting settlement) events."""
        result = await db.execute(
            select(Event)
            .where(Event.status == "closed")
            .order_by(Event.close_time)
        )
        return list(result.scalars().all())

    async def get_events_by_date(
        self, db: AsyncSession, selection_date: date
    ) -> list[Event]:
        """Fetch events by selection date."""
        result = await db.execute(
            select(Event)
            .where(Event.selection_date == selection_date)
            .order_by(Event.close_time)
        )
        return list(result.scalars().all())

    async def update_event_price(
        self,
        db: AsyncSession,
        event_id: UUID,
        price: Decimal,
    ) -> Event:
        """Update current price from Kalshi feed."""
        event = await self.get_event(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        event.current_price = price
        await db.commit()
        await db.refresh(event)
        return event

    async def update_viewer_count(
        self,
        db: AsyncSession,
        event_id: UUID,
        count: int,
    ) -> None:
        """Update viewer count for an event."""
        await db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(viewers=count)
        )
        await db.commit()

    async def check_and_close_expired_events(self, db: AsyncSession) -> list[Event]:
        """Check for events past close time and close them."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Event)
            .where(Event.status == "active")
            .where(Event.close_time <= now)
        )
        expired_events = list(result.scalars().all())

        closed = []
        for event in expired_events:
            event.status = "closed"
            closed.append(event)
            logger.info(f"Auto-closed expired event: {event.title}")

        if closed:
            await db.commit()

        return closed


# Singleton instance
event_service = EventService()
