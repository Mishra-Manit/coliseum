"""AI Models API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db
from schemas import (
    AIModelPerformanceResponse,
    AIModelResponse,
    BetDetailResponse,
)
from services import ai_model_service, bet_service

router = APIRouter(prefix="/models", tags=["AI Models"])


@router.get("/", response_model=list[AIModelResponse])
async def list_models(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all AI models."""
    if include_inactive:
        models = await ai_model_service.get_all_models(db)
    else:
        models = await ai_model_service.get_all_active_models(db)

    return [AIModelResponse.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed AI model information."""
    model = await ai_model_service.get_model(db, model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return AIModelResponse.model_validate(model)


@router.get("/{model_id}/bets", response_model=list)
async def get_model_bets(
    model_id: UUID,
    settled: Optional[bool] = None,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get betting history for a model."""
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    bets = await bet_service.get_model_bets(db, model_id, settled=settled, limit=limit)

    return [
        {
            "id": str(bet.id),
            "event_id": str(bet.event_id),
            "position": bet.position,
            "amount": float(bet.amount),
            "price": float(bet.price),
            "shares": bet.shares,
            "pnl": float(bet.pnl) if bet.pnl else None,
            "settled": bet.settled,
            "settled_at": bet.settled_at.isoformat() if bet.settled_at else None,
            "created_at": bet.created_at.isoformat(),
        }
        for bet in bets
    ]


@router.get("/{model_id}/performance", response_model=AIModelPerformanceResponse)
async def get_model_performance(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get performance metrics for a model."""
    model = await ai_model_service.get_model(db, model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Calculate additional metrics
    win_rate = None
    if model.total_bets > 0:
        win_rate = (model.win_count / model.total_bets) * 100

    average_bet_size = None
    if model.total_bets > 0:
        # Get all bets to calculate average
        bets = await bet_service.get_model_bets(db, model_id, limit=1000)
        if bets:
            total_amount = sum(float(b.amount) for b in bets)
            average_bet_size = total_amount / len(bets)

    return AIModelPerformanceResponse(
        id=model.id,
        name=model.name,
        balance=model.balance,
        initial_balance=model.initial_balance,
        total_pnl=model.total_pnl,
        roi_percentage=model.roi_percentage,
        win_count=model.win_count,
        loss_count=model.loss_count,
        abstain_count=model.abstain_count,
        total_bets=model.total_bets,
        win_rate=win_rate,
        average_bet_size=average_bet_size,
    )
