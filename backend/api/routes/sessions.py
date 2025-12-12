"""Betting Sessions API routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db
from schemas import (
    BettingSessionDetailResponse,
    SessionMessageResponse,
)
from services import betting_session_service

router = APIRouter(prefix="/sessions", tags=["Betting Sessions"])


@router.get("/{session_id}", response_model=BettingSessionDetailResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get betting session details."""
    session = await betting_session_service.get_session_with_details(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Count messages
    messages = await betting_session_service.get_session_messages(db, session_id)

    return BettingSessionDetailResponse(
        id=session.id,
        event_id=session.event_id,
        model_id=session.model_id,
        status=session.status,
        final_position=session.final_position,
        bet_amount=session.bet_amount,
        confidence_score=session.confidence_score,
        reasoning_summary=session.reasoning_summary,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        model_name=session.model.name if session.model else "Unknown",
        model_color=session.model.color if session.model else "bg-gray-500",
        model_avatar=session.model.avatar if session.model else "??",
        event_title=session.event.title if session.event else "Unknown Event",
        messages_count=len(messages),
    )


@router.get("/{session_id}/messages", response_model=list[SessionMessageResponse])
async def get_session_messages(
    session_id: UUID,
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get messages from a betting session."""
    session = await betting_session_service.get_session_with_details(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await betting_session_service.get_session_messages(
        db, session_id, since=since
    )

    return [
        SessionMessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            message_type=msg.message_type,
            content=msg.content,
            action={
                "type": msg.action_type,
                "amount": msg.action_amount,
                "shares": msg.action_shares,
                "price": msg.action_price,
            } if msg.action_type else None,
            sequence_number=msg.sequence_number,
            created_at=msg.created_at,
            model_id=session.model_id,
            model_name=session.model.name if session.model else None,
            model_color=session.model.color if session.model else None,
            model_avatar=session.model.avatar if session.model else None,
        )
        for msg in messages
    ]
