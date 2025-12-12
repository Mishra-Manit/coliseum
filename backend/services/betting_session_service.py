"""Betting session orchestration service."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import AIModel, BettingSession, Event, EventSummary, SessionMessage
from services.ai_model_service import ai_model_service
from services.bet_service import bet_service
from utils.llm_agent import run_agent

logger = logging.getLogger(__name__)


# Position sizing constants
KELLY_FRACTION = Decimal("0.25")  # Conservative Kelly
MAX_BET_PERCENTAGE = Decimal("0.10")  # Max 10% of balance
MIN_BET_AMOUNT = Decimal("100")  # Minimum $100


class BettingSessionService:
    """
    Orchestrates AI model betting sessions.
    Manages the decision-making process and message generation.
    """

    async def create_session(
        self,
        db: AsyncSession,
        event_id: UUID,
        model_id: UUID,
    ) -> BettingSession:
        """Initialize a new betting session."""
        # Check if session already exists
        result = await db.execute(
            select(BettingSession)
            .where(BettingSession.event_id == event_id)
            .where(BettingSession.model_id == model_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        session = BettingSession(
            event_id=event_id,
            model_id=model_id,
            status="pending",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def run_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        broadcast_callback=None,
    ) -> BettingSession:
        """
        Execute the AI betting session.

        Process:
        1. Load event and summary context
        2. Initialize AI agent with model-specific prompt
        3. Generate reasoning messages
        4. Make final decision: BET YES, BET NO, or ABSTAIN
        5. Calculate position size if betting
        6. Execute bet through BetService
        7. Store final reasoning summary
        """
        # Load session with related data
        result = await db.execute(
            select(BettingSession)
            .options(
                selectinload(BettingSession.event).selectinload(Event.summary),
                selectinload(BettingSession.model),
            )
            .where(BettingSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        event = session.event
        model = session.model
        summary = event.summary

        # Update session status
        session.status = "running"
        session.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(event, summary, model)

            # Generate reasoning
            reasoning_result = await self._generate_reasoning(
                db,
                session,
                model,
                system_prompt,
                broadcast_callback,
            )

            # Parse decision
            decision = reasoning_result.get("decision", "ABSTAIN")
            confidence = Decimal(str(reasoning_result.get("confidence", 0.5)))
            reasoning_text = reasoning_result.get("reasoning", "")

            # Update session
            session.final_position = decision
            session.confidence_score = confidence
            session.reasoning_summary = reasoning_text

            # Execute bet if not abstaining
            if decision in ("YES", "NO") and model.is_active and model.balance > MIN_BET_AMOUNT:
                bet_amount = self._calculate_position_size(
                    model, confidence, event.current_price
                )

                if bet_amount >= MIN_BET_AMOUNT:
                    session.bet_amount = bet_amount

                    bet = await bet_service.place_bet(
                        db=db,
                        session_id=session_id,
                        model_id=model.id,
                        event_id=event.id,
                        position=decision,
                        amount=bet_amount,
                        price=event.current_price,
                    )

                    # Add action message
                    await self.add_message(
                        db=db,
                        session_id=session_id,
                        content=f"Placing bet: {decision} ${bet_amount:.2f} @ {float(event.current_price):.2%}",
                        message_type="action",
                        action_type="BUY",
                        action_amount=bet_amount,
                        action_shares=bet.shares,
                        action_price=event.current_price,
                        broadcast_callback=broadcast_callback,
                    )
            else:
                # Record abstain
                await ai_model_service.record_abstain(db, model.id)

            # Complete session
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(session)

            logger.info(
                f"Session completed: {model.name} -> {decision} "
                f"(confidence: {confidence:.2%})"
            )
            return session

        except Exception as e:
            logger.error(f"Session {session_id} failed: {e}")
            session.status = "failed"
            session.completed_at = datetime.now(timezone.utc)
            await db.commit()
            raise

    def _build_system_prompt(
        self,
        event: Event,
        summary: Optional[EventSummary],
        model: AIModel,
    ) -> str:
        """Build system prompt for AI model."""
        summary_text = summary.summary_text if summary else "No summary available."
        key_factors = summary.key_factors if summary else []

        factors_text = "\n".join(
            f"- {f.get('factor', 'Unknown')} ({f.get('impact', 'neutral')})"
            for f in key_factors
        )

        return f"""You are {model.name}, a competitive AI prediction market trader in the Coliseum arena.

PERSONALITY: You are confident, competitive, and entertaining. You trash-talk other AI models,
make bold predictions, and bring sports commentator energy. Think ESPN meets Wall Street.

YOUR CURRENT STATUS:
- Balance: ${model.balance:,.2f}
- Total P&L: ${model.total_pnl:,.2f}
- Win/Loss: {model.win_count}/{model.loss_count}
- ROI: {model.roi_percentage:.2f}%

EVENT DETAILS:
- Title: {event.title}
- Question: {event.question}
- Category: {event.category}
- Current Market Price: {float(event.current_price) * 100:.1f}% YES

MARKET CONTEXT:
{event.market_context or "No additional context."}

RESEARCH SUMMARY:
{summary_text}

KEY FACTORS:
{factors_text or "No key factors identified."}

BETTING RULES:
- You can bet YES, NO, or ABSTAIN
- Minimum bet: $100
- Maximum bet: 10% of your balance (${float(model.balance) * 0.1:,.2f})
- If your balance hits $0, you're eliminated from the arena

YOUR TASK:
1. Analyze the event and form an opinion
2. Generate 3-5 reasoning messages (be entertaining and competitive!)
3. Make your final decision: YES, NO, or ABSTAIN
4. If betting, specify your confidence (0.0-1.0)

OUTPUT FORMAT (JSON):
{{
    "messages": [
        "Your first reasoning message (be entertaining!)",
        "Your second reasoning message (trash-talk other models!)",
        "Your final analysis"
    ],
    "decision": "YES" | "NO" | "ABSTAIN",
    "confidence": 0.0-1.0,
    "reasoning": "Brief summary of your reasoning"
}}

Remember: You're performing for an audience. Be bold, be confident, be entertaining!"""

    async def _generate_reasoning(
        self,
        db: AsyncSession,
        session: BettingSession,
        model: AIModel,
        system_prompt: str,
        broadcast_callback=None,
    ) -> dict:
        """Generate AI reasoning and decision."""
        try:
            result = await run_agent(
                prompt=system_prompt,
                model=model.openrouter_model,
                max_tokens=1500,
                temperature=0.8,  # Higher temp for more personality
            )

            # Parse JSON response
            import json
            data = json.loads(result)

            # Store messages
            messages = data.get("messages", [])
            for i, msg in enumerate(messages):
                await self.add_message(
                    db=db,
                    session_id=session.id,
                    content=msg,
                    message_type="reasoning",
                    broadcast_callback=broadcast_callback,
                )

            return data

        except Exception as e:
            logger.error(f"AI reasoning generation failed: {e}")
            # Return default abstain
            return {
                "messages": [f"Technical difficulties... {model.name} is sitting this one out."],
                "decision": "ABSTAIN",
                "confidence": 0.0,
                "reasoning": f"Error during analysis: {str(e)}",
            }

    def _calculate_position_size(
        self,
        model: AIModel,
        confidence: Decimal,
        current_price: Decimal,
    ) -> Decimal:
        """
        Calculate bet amount using fractional Kelly Criterion.

        position_size = balance * kelly_fraction * confidence
        Constrained by max/min limits.
        """
        # Kelly calculation (simplified)
        position_size = model.balance * KELLY_FRACTION * confidence

        # Apply constraints
        max_bet = model.balance * MAX_BET_PERCENTAGE
        position_size = min(position_size, max_bet)
        position_size = max(position_size, MIN_BET_AMOUNT)

        # Can't bet more than balance
        position_size = min(position_size, model.balance)

        return position_size.quantize(Decimal("0.01"))

    async def add_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        content: str,
        message_type: str = "reasoning",
        action_type: Optional[str] = None,
        action_amount: Optional[Decimal] = None,
        action_shares: Optional[int] = None,
        action_price: Optional[Decimal] = None,
        broadcast_callback=None,
    ) -> SessionMessage:
        """Add a message to the session and optionally broadcast."""
        # Get next sequence number
        result = await db.execute(
            select(func.coalesce(func.max(SessionMessage.sequence_number), 0))
            .where(SessionMessage.session_id == session_id)
        )
        next_seq = result.scalar() + 1

        message = SessionMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            action_type=action_type,
            action_amount=action_amount,
            action_shares=action_shares,
            action_price=action_price,
            sequence_number=next_seq,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Broadcast if callback provided
        if broadcast_callback:
            await broadcast_callback(message)

        return message

    async def get_session(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[BettingSession]:
        """Get session by ID."""
        result = await db.execute(
            select(BettingSession).where(BettingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_with_details(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[BettingSession]:
        """Get session with model and event details."""
        result = await db.execute(
            select(BettingSession)
            .options(
                selectinload(BettingSession.model),
                selectinload(BettingSession.event),
                selectinload(BettingSession.messages),
            )
            .where(BettingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_event_sessions(
        self, db: AsyncSession, event_id: UUID
    ) -> list[BettingSession]:
        """Get all sessions for an event."""
        result = await db.execute(
            select(BettingSession)
            .options(selectinload(BettingSession.model))
            .where(BettingSession.event_id == event_id)
            .order_by(BettingSession.created_at)
        )
        return list(result.scalars().all())

    async def get_session_messages(
        self,
        db: AsyncSession,
        session_id: UUID,
        since: Optional[datetime] = None,
    ) -> list[SessionMessage]:
        """Get messages for a session."""
        query = (
            select(SessionMessage)
            .where(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.sequence_number)
        )

        if since:
            query = query.where(SessionMessage.created_at > since)

        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance
betting_session_service = BettingSessionService()
