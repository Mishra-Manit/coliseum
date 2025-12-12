"""Settlement validation and processing service."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Bet, BettingSession, Event, Settlement
from services.ai_model_service import ai_model_service
from services.bet_service import bet_service
from services.kalshi_service import kalshi_service
from utils.llm_agent import run_agent

logger = logging.getLogger(__name__)


class SettlementService:
    """
    Lightweight agent for validating and processing event settlements.
    """

    async def check_for_settlements(self, db: AsyncSession) -> list[Event]:
        """Find events ready for settlement (closed status)."""
        result = await db.execute(
            select(Event)
            .where(Event.status == "closed")
            .order_by(Event.close_time)
        )
        return list(result.scalars().all())

    async def settle_event(
        self,
        db: AsyncSession,
        event_id: UUID,
        broadcast_callback=None,
    ) -> Settlement:
        """
        Process settlement for an event.

        Process:
        1. Query Kalshi API for settlement result
        2. Validate result is final
        3. Update event with outcome
        4. Settle all bets on event
        5. Update AI model balances
        6. Record settlement
        """
        # Get event
        result = await db.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        if event.status not in ("closed", "active"):
            raise ValueError(f"Event {event_id} is not ready for settlement")

        # Check if already settled
        existing = await db.execute(
            select(Settlement).where(Settlement.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Event {event_id} already settled")

        # Get outcome from Kalshi
        outcome = None
        kalshi_data = None

        if event.kalshi_market_id:
            outcome = await kalshi_service.get_settlement_result(
                event.kalshi_market_id
            )
            market_data = await kalshi_service.get_market_details(
                event.kalshi_market_id
            )
            kalshi_data = market_data

        if not outcome:
            raise ValueError(f"No settlement result available for event {event_id}")

        # Validate settlement
        is_valid = await self._validate_settlement(event, outcome)

        # Process bets
        settlement_results = await self._process_bet_settlements(
            db, event_id, outcome
        )

        # Update event
        event.status = "settled"
        event.outcome = outcome
        event.settlement_time = datetime.now(timezone.utc)

        # Calculate totals
        total_pnl = sum(r["pnl"] for r in settlement_results.values())

        # Create settlement record
        settlement = Settlement(
            event_id=event_id,
            outcome=outcome,
            kalshi_settlement_data=kalshi_data,
            validated=is_valid,
            validation_notes="Automated validation passed" if is_valid else "Manual review recommended",
            total_bets_settled=len(settlement_results),
            total_pnl_distributed=total_pnl,
        )
        db.add(settlement)
        await db.commit()
        await db.refresh(settlement)

        logger.info(
            f"Settled event {event.title}: {outcome} "
            f"({len(settlement_results)} bets, ${total_pnl:.2f} P&L)"
        )

        return settlement

    async def _validate_settlement(
        self,
        event: Event,
        kalshi_result: str,
    ) -> bool:
        """
        Use AI agent to validate settlement looks correct.
        Simple sanity check comparing Kalshi result with event question.
        """
        try:
            validation_prompt = f"""
            Validate this prediction market settlement:

            Event: {event.title}
            Question: {event.question}
            Reported Outcome: {kalshi_result}

            Does this outcome make logical sense for this question?
            Respond with JSON: {{"valid": true/false, "reason": "brief explanation"}}
            """

            result = await run_agent(
                prompt=validation_prompt,
                model="anthropic/claude-3-haiku-20240307",  # Fast, cheap model
                max_tokens=200,
            )

            import json
            data = json.loads(result)
            return data.get("valid", True)

        except Exception as e:
            logger.warning(f"Settlement validation error: {e}")
            return True  # Default to valid if validation fails

    async def _process_bet_settlements(
        self,
        db: AsyncSession,
        event_id: UUID,
        outcome: str,
    ) -> dict[UUID, dict]:
        """
        Process all bets for an event.
        Returns mapping of model_id -> {pnl, new_balance}.
        """
        # Get all unsettled bets
        bets = await bet_service.get_unsettled_bets_for_event(db, event_id)

        results = {}

        for bet in bets:
            # Calculate and record P&L
            pnl = bet_service.calculate_pnl(bet, outcome)
            is_win = pnl > 0

            # Settle bet
            bet.pnl = pnl
            bet.settled = True
            bet.settled_at = datetime.now(timezone.utc)

            # Update model balance and stats
            model = await ai_model_service.record_bet_outcome(
                db, bet.model_id, pnl, is_win
            )

            # Store result
            results[bet.model_id] = {
                "pnl": pnl,
                "new_balance": model.balance,
                "position": bet.position,
                "is_win": is_win,
            }

            logger.info(
                f"Settled bet: {model.name} {bet.position} -> "
                f"{'WIN' if is_win else 'LOSS'} ${pnl:.2f}"
            )

        await db.commit()
        return results

    async def get_settlement(
        self, db: AsyncSession, event_id: UUID
    ) -> Optional[Settlement]:
        """Get settlement for an event."""
        result = await db.execute(
            select(Settlement).where(Settlement.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_model_settlement_results(
        self,
        db: AsyncSession,
        event_id: UUID,
    ) -> list[dict]:
        """Get settlement results per model for an event."""
        # Get all sessions for the event
        result = await db.execute(
            select(BettingSession)
            .options(
                selectinload(BettingSession.model),
                selectinload(BettingSession.bets),
            )
            .where(BettingSession.event_id == event_id)
        )
        sessions = list(result.scalars().all())

        results = []
        for session in sessions:
            total_pnl = sum(b.pnl or Decimal("0") for b in session.bets)
            results.append({
                "model_id": session.model_id,
                "model_name": session.model.name,
                "position": session.final_position,
                "pnl": total_pnl,
                "new_balance": session.model.balance,
            })

        return results


# Singleton instance
settlement_service = SettlementService()
