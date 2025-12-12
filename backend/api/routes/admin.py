"""Admin API routes."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db
from schemas import (
    AdminActionResponse,
    AdminEventApproveRequest,
    AdminEventManualRequest,
    AdminEventSelectRequest,
    AdminEventSelectResponse,
    AdminModelResetRequest,
)
from services import ai_model_service, event_service
from tasks import select_daily_events, activate_event

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/events/select", response_model=AdminEventSelectResponse)
async def trigger_event_selection(
    request: AdminEventSelectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual event selection."""
    selection_date = request.date or date.today()

    # Run selection
    events = await event_service.select_daily_events(
        db,
        count=request.count,
        selection_date=selection_date,
    )

    return AdminEventSelectResponse(
        events_selected=len(events),
        event_ids=[e.id for e in events],
        message=f"Selected {len(events)} events for {selection_date}",
    )


@router.post("/events/manual", response_model=AdminActionResponse)
async def add_manual_event(
    request: AdminEventManualRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a specific Kalshi event manually."""
    event = await event_service.add_manual_event(
        db,
        kalshi_market_id=request.kalshi_market_id,
        selection_date=request.selection_date,
    )

    if not event:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find market: {request.kalshi_market_id}",
        )

    await db.commit()

    return AdminActionResponse(
        success=True,
        message=f"Added event: {event.title}",
        data={"event_id": str(event.id)},
    )


@router.get("/events/pending")
async def get_pending_events(db: AsyncSession = Depends(get_db)):
    """View today's pending event selections."""
    events = await event_service.get_pending_events(db)

    return {
        "count": len(events),
        "events": [
            {
                "id": str(e.id),
                "title": e.title,
                "category": e.category,
                "current_price": float(e.current_price),
                "close_time": e.close_time.isoformat(),
                "kalshi_market_id": e.kalshi_market_id,
            }
            for e in events
        ],
    }


@router.post("/events/approve", response_model=AdminActionResponse)
async def approve_events(
    request: AdminEventApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve and activate pending events."""
    activated = []

    for event_id in request.event_ids:
        try:
            event = await event_service.activate_event(db, event_id)
            activated.append(str(event.id))
        except ValueError as e:
            # Skip events that can't be activated
            pass

    return AdminActionResponse(
        success=True,
        message=f"Activated {len(activated)} events",
        data={"event_ids": activated},
    )


@router.put("/events/{event_id}/swap", response_model=AdminActionResponse)
async def swap_event(
    event_id: UUID,
    new_kalshi_market_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Swap a pending event for a different one."""
    # Get current event
    event = await event_service.get_event(db, event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Can only swap pending events",
        )

    # Delete old event
    await db.delete(event)

    # Add new event
    new_event = await event_service.add_manual_event(
        db,
        kalshi_market_id=new_kalshi_market_id,
        selection_date=event.selection_date,
    )

    if not new_event:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Could not find market: {new_kalshi_market_id}",
        )

    await db.commit()

    return AdminActionResponse(
        success=True,
        message=f"Swapped event. New: {new_event.title}",
        data={
            "old_event_id": str(event_id),
            "new_event_id": str(new_event.id),
        },
    )


@router.post("/models/{model_id}/reset", response_model=AdminActionResponse)
async def reset_model_balance(
    model_id: UUID,
    request: AdminModelResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Emergency balance reset for a model."""
    model = await ai_model_service.get_model(db, model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    old_balance = model.balance

    model = await ai_model_service.reset_model_balance(
        db, model_id, request.new_balance
    )

    return AdminActionResponse(
        success=True,
        message=f"Reset {model.name} balance: ${old_balance} -> ${request.new_balance}. Reason: {request.reason}",
        data={
            "model_id": str(model.id),
            "old_balance": float(old_balance),
            "new_balance": float(model.balance),
        },
    )


@router.post("/models/initialize", response_model=AdminActionResponse)
async def initialize_all_models(db: AsyncSession = Depends(get_db)):
    """Initialize or update all AI models in the database."""
    models = await ai_model_service.initialize_models(db)

    return AdminActionResponse(
        success=True,
        message=f"Initialized {len(models)} AI models",
        data={
            "model_ids": [str(m.id) for m in models],
            "models": [m.name for m in models],
        },
    )
