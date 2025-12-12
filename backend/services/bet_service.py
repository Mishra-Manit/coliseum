"""Bet execution and tracking service."""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Bet, BettingSession, Event, AIModel
from services.ai_model_service import ai_model_service

logger = logging.getLogger(__name__)


class BetService:
    """
    Handles bet placement, tracking, and settlement calculations.
    """

    async def place_bet(
        self,
        db: AsyncSession,
        session_id: UUID,
        model_id: UUID,
        event_id: UUID,
        position: str,
        amount: Decimal,
        price: Decimal,
    ) -> Bet:
        """
        Place a bet for an AI model.

        Process:
        1. Validate model has sufficient balance
        2. Calculate shares: amount / price
        3. Debit model balance
        4. Create bet record
        """
        # Get model
        model = await ai_model_service.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Validate balance
        if model.balance < amount:
            raise ValueError(
                f"Insufficient balance: ${model.balance} < ${amount}"
            )

        # Calculate shares
        shares = int(amount / price)
        if shares <= 0:
            raise ValueError("Amount too small for any shares")

        # Debit balance
        await ai_model_service.update_balance(
            db, model_id, amount, is_credit=False
        )

        # Create bet record
        bet = Bet(
            session_id=session_id,
            model_id=model_id,
            event_id=event_id,
            position=position,
            amount=amount,
            price=price,
            shares=shares,
        )
        db.add(bet)
        await db.commit()
        await db.refresh(bet)

        logger.info(
            f"Placed bet: {model.name} {position} ${amount} @ {price} "
            f"({shares} shares)"
        )
        return bet

    async def get_bet(self, db: AsyncSession, bet_id: UUID) -> Optional[Bet]:
        """Get a bet by ID."""
        result = await db.execute(select(Bet).where(Bet.id == bet_id))
        return result.scalar_one_or_none()

    async def get_model_bets_for_event(
        self,
        db: AsyncSession,
        model_id: UUID,
        event_id: UUID,
    ) -> list[Bet]:
        """Get all bets a model has on an event."""
        result = await db.execute(
            select(Bet)
            .where(Bet.model_id == model_id)
            .where(Bet.event_id == event_id)
            .order_by(Bet.created_at)
        )
        return list(result.scalars().all())

    async def get_event_bets(self, db: AsyncSession, event_id: UUID) -> list[Bet]:
        """Get all bets on an event across all models."""
        result = await db.execute(
            select(Bet)
            .options(selectinload(Bet.model))
            .where(Bet.event_id == event_id)
            .order_by(Bet.created_at)
        )
        return list(result.scalars().all())

    async def get_unsettled_bets_for_event(
        self, db: AsyncSession, event_id: UUID
    ) -> list[Bet]:
        """Get all unsettled bets for an event."""
        result = await db.execute(
            select(Bet)
            .options(selectinload(Bet.model))
            .where(Bet.event_id == event_id)
            .where(Bet.settled == False)
        )
        return list(result.scalars().all())

    async def get_model_bets(
        self,
        db: AsyncSession,
        model_id: UUID,
        settled: Optional[bool] = None,
        limit: int = 100,
    ) -> list[Bet]:
        """Get betting history for a model."""
        query = select(Bet).where(Bet.model_id == model_id)

        if settled is not None:
            query = query.where(Bet.settled == settled)

        query = query.order_by(Bet.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    def calculate_pnl(self, bet: Bet, outcome: str) -> Decimal:
        """
        Calculate P&L for a bet given the outcome.

        If position matches outcome:
            pnl = shares * (1 - entry_price)  # Win: gain the spread
        If position doesn't match:
            pnl = -amount  # Lose entire bet
        """
        if bet.position == outcome:
            # Winner: profit = shares * (1 - price)
            pnl = Decimal(bet.shares) * (Decimal("1") - bet.price)
        else:
            # Loser: lose entire bet amount
            pnl = -bet.amount

        return pnl.quantize(Decimal("0.01"))

    async def settle_bet(
        self,
        db: AsyncSession,
        bet_id: UUID,
        outcome: str,
    ) -> Bet:
        """
        Settle a single bet.

        Calculates P&L and updates the bet record.
        Does NOT update model balance (done by settlement_service).
        """
        bet = await self.get_bet(db, bet_id)
        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        if bet.settled:
            raise ValueError(f"Bet {bet_id} already settled")

        # Calculate P&L
        pnl = self.calculate_pnl(bet, outcome)

        # Update bet
        bet.pnl = pnl
        bet.settled = True
        from datetime import datetime, timezone
        bet.settled_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(bet)

        logger.info(
            f"Settled bet {bet_id}: {bet.position} vs {outcome} = ${pnl}"
        )
        return bet

    async def get_model_position_on_event(
        self,
        db: AsyncSession,
        model_id: UUID,
        event_id: UUID,
    ) -> dict:
        """
        Get aggregated position for a model on an event.
        Returns: {position, shares, avg_price, pnl}
        """
        bets = await self.get_model_bets_for_event(db, model_id, event_id)

        if not bets:
            return {
                "position": None,
                "shares": 0,
                "avg_price": Decimal("0"),
                "pnl": None,
            }

        # Calculate aggregates
        total_shares = sum(b.shares for b in bets)
        total_amount = sum(b.amount for b in bets)
        avg_price = total_amount / total_shares if total_shares > 0 else Decimal("0")
        total_pnl = sum(b.pnl for b in bets if b.pnl is not None)

        # Assume all bets are same position (simplification)
        position = bets[0].position

        return {
            "position": position,
            "shares": total_shares,
            "avg_price": avg_price.quantize(Decimal("0.0001")),
            "pnl": total_pnl if any(b.settled for b in bets) else None,
        }


# Singleton instance
bet_service = BetService()
