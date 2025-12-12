"""Leaderboard API routes."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db
from schemas import LeaderboardResponse
from services import leaderboard_service

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    """Get current overall leaderboard."""
    entries = await leaderboard_service.get_current_leaderboard(db)

    return LeaderboardResponse(
        entries=entries,
        as_of=datetime.utcnow(),
    )


@router.get("/daily")
async def get_daily_leaderboard(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get leaderboard for a specific day."""
    entries = await leaderboard_service.get_daily_leaderboard(db, target_date)

    return {
        "date": (target_date or date.today()).isoformat(),
        "entries": entries,
    }


@router.get("/history")
async def get_leaderboard_history(
    days: int = Query(7, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get historical leaderboard data."""
    history = await leaderboard_service.get_leaderboard_history(db, days=days)

    return {
        "days": days,
        "history": history,
    }
