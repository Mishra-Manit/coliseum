"""Events API routes."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.dependencies import get_db
from models import Event, PriceHistory
from schemas import (
    EventBriefResponse,
    EventDetailResponse,
    EventResponse,
    EventStatus,
    EventSummaryResponse,
    ModelPositionResponse,
    PriceHistoryResponse,
)
from services import bet_service, event_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=list[EventBriefResponse])
async def list_events(
    status: Optional[EventStatus] = None,
    selection_date: Optional[date] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List events with optional filtering."""
    query = select(Event)

    if status:
        query = query.where(Event.status == status.value)

    if selection_date:
        query = query.where(Event.selection_date == selection_date)

    query = query.order_by(Event.close_time.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    events = list(result.scalars().all())

    return [EventBriefResponse.model_validate(e) for e in events]


@router.get("/active", response_model=list[EventResponse])
async def get_active_events(db: AsyncSession = Depends(get_db)):
    """Get all currently active events."""
    events = await event_service.get_active_events(db)
    return [EventResponse.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed event information including summary."""
    event = await event_service.get_event_with_summary(db, event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get model positions
    from services import ai_model_service
    models = await ai_model_service.get_all_models(db)

    positions = []
    for model in models:
        pos = await bet_service.get_model_position_on_event(db, model.id, event_id)
        positions.append(
            ModelPositionResponse(
                model_id=model.id,
                model_name=model.name,
                model_color=model.color,
                model_avatar=model.avatar,
                position=pos["position"],
                shares=pos["shares"],
                avg_price=pos["avg_price"],
                pnl=pos["pnl"],
            )
        )

    response = EventDetailResponse.model_validate(event)
    response.summary = (
        EventSummaryResponse.model_validate(event.summary) if event.summary else None
    )
    response.model_positions = positions

    return response


@router.get("/{event_id}/summary", response_model=EventSummaryResponse)
async def get_event_summary(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the generated summary for an event."""
    from services import summary_service

    summary = await summary_service.get_summary(db, event_id)

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return EventSummaryResponse.model_validate(summary)


@router.get("/{event_id}/bets", response_model=list)
async def get_event_bets(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all bets placed on an event."""
    bets = await bet_service.get_event_bets(db, event_id)

    return [
        {
            "id": str(bet.id),
            "model_id": str(bet.model_id),
            "model_name": bet.model.name if bet.model else None,
            "position": bet.position,
            "amount": float(bet.amount),
            "price": float(bet.price),
            "shares": bet.shares,
            "pnl": float(bet.pnl) if bet.pnl else None,
            "settled": bet.settled,
            "created_at": bet.created_at.isoformat(),
        }
        for bet in bets
    ]


@router.get("/{event_id}/sessions", response_model=list)
async def get_event_sessions(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all AI betting sessions for an event."""
    from services import betting_session_service

    sessions = await betting_session_service.get_event_sessions(db, event_id)

    return [
        {
            "id": str(session.id),
            "model_id": str(session.model_id),
            "model_name": session.model.name if session.model else None,
            "model_color": session.model.color if session.model else None,
            "model_avatar": session.model.avatar if session.model else None,
            "status": session.status,
            "final_position": session.final_position,
            "bet_amount": float(session.bet_amount) if session.bet_amount else None,
            "confidence_score": float(session.confidence_score) if session.confidence_score else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }
        for session in sessions
    ]


@router.get("/{event_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(
    event_id: UUID,
    period: str = Query("1d", pattern="^(1h|1d|1w)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical price data for an event."""
    from datetime import timedelta

    now = datetime.utcnow()
    if period == "1h":
        start = now - timedelta(hours=1)
    elif period == "1d":
        start = now - timedelta(days=1)
    else:  # 1w
        start = now - timedelta(weeks=1)

    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.event_id == event_id)
        .where(PriceHistory.recorded_at >= start)
        .order_by(PriceHistory.recorded_at)
    )
    history = list(result.scalars().all())

    return [PriceHistoryResponse.model_validate(h) for h in history]
