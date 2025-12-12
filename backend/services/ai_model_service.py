"""AI Model management service."""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AIModel

logger = logging.getLogger(__name__)


# AI Models configuration
AI_MODELS_CONFIG = [
    {
        "external_id": "gpt-4o",
        "name": "GPT-4o",
        "openrouter_model": "openai/gpt-4o",
        "color": "bg-green-500",
        "text_color": "text-green-500",
        "avatar": "GPT",
    },
    {
        "external_id": "claude-3.5",
        "name": "Claude 3.5",
        "openrouter_model": "anthropic/claude-3.5-sonnet",
        "color": "bg-orange-500",
        "text_color": "text-orange-500",
        "avatar": "CL",
    },
    {
        "external_id": "grok-2",
        "name": "Grok-2",
        "openrouter_model": "x-ai/grok-2",
        "color": "bg-blue-500",
        "text_color": "text-blue-500",
        "avatar": "GK",
    },
    {
        "external_id": "gemini-pro",
        "name": "Gemini Pro",
        "openrouter_model": "google/gemini-pro-1.5",
        "color": "bg-purple-500",
        "text_color": "text-purple-500",
        "avatar": "GM",
    },
    {
        "external_id": "llama-3.1",
        "name": "Llama 3.1",
        "openrouter_model": "meta-llama/llama-3.1-405b-instruct",
        "color": "bg-red-500",
        "text_color": "text-red-500",
        "avatar": "LL",
    },
    {
        "external_id": "mistral",
        "name": "Mistral Large",
        "openrouter_model": "mistralai/mistral-large",
        "color": "bg-cyan-500",
        "text_color": "text-cyan-500",
        "avatar": "MS",
    },
    {
        "external_id": "deepseek",
        "name": "DeepSeek V2",
        "openrouter_model": "deepseek/deepseek-chat",
        "color": "bg-yellow-500",
        "text_color": "text-yellow-500",
        "avatar": "DS",
    },
    {
        "external_id": "qwen",
        "name": "Qwen Max",
        "openrouter_model": "qwen/qwen-2-72b-instruct",
        "color": "bg-pink-500",
        "text_color": "text-pink-500",
        "avatar": "QW",
    },
]


class AIModelService:
    """
    Manages AI model configuration, balance tracking, and performance metrics.
    """

    INITIAL_BALANCE = Decimal("100000.00")

    async def initialize_models(self, db: AsyncSession) -> list[AIModel]:
        """Create or update all 8 AI models in database."""
        models = []

        for config in AI_MODELS_CONFIG:
            # Check if model exists
            result = await db.execute(
                select(AIModel).where(AIModel.external_id == config["external_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update config fields (not balance/stats)
                existing.name = config["name"]
                existing.openrouter_model = config["openrouter_model"]
                existing.color = config["color"]
                existing.text_color = config["text_color"]
                existing.avatar = config["avatar"]
                models.append(existing)
            else:
                # Create new model
                model = AIModel(
                    external_id=config["external_id"],
                    name=config["name"],
                    openrouter_model=config["openrouter_model"],
                    color=config["color"],
                    text_color=config["text_color"],
                    avatar=config["avatar"],
                    balance=self.INITIAL_BALANCE,
                    initial_balance=self.INITIAL_BALANCE,
                )
                db.add(model)
                models.append(model)

        await db.commit()
        logger.info(f"Initialized {len(models)} AI models")
        return models

    async def get_model(self, db: AsyncSession, model_id: UUID) -> Optional[AIModel]:
        """Fetch single model by ID."""
        result = await db.execute(select(AIModel).where(AIModel.id == model_id))
        return result.scalar_one_or_none()

    async def get_model_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Optional[AIModel]:
        """Fetch single model by external ID."""
        result = await db.execute(
            select(AIModel).where(AIModel.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_all_models(self, db: AsyncSession) -> list[AIModel]:
        """Fetch all AI models."""
        result = await db.execute(select(AIModel).order_by(AIModel.name))
        return list(result.scalars().all())

    async def get_all_active_models(self, db: AsyncSession) -> list[AIModel]:
        """Fetch all active AI models."""
        result = await db.execute(
            select(AIModel)
            .where(AIModel.is_active == True)
            .order_by(AIModel.name)
        )
        return list(result.scalars().all())

    async def update_balance(
        self,
        db: AsyncSession,
        model_id: UUID,
        amount: Decimal,
        is_credit: bool,
    ) -> AIModel:
        """Credit or debit model balance."""
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        if is_credit:
            model.balance += amount
        else:
            model.balance -= amount
            # Check if eliminated
            if model.balance <= 0:
                model.balance = Decimal("0.00")
                model.is_active = False
                logger.warning(f"Model {model.name} eliminated (balance: $0)")

        await db.commit()
        await db.refresh(model)
        return model

    async def record_bet_outcome(
        self,
        db: AsyncSession,
        model_id: UUID,
        pnl: Decimal,
        is_win: bool,
    ) -> AIModel:
        """Update model statistics after bet settlement."""
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Update P&L
        model.total_pnl += pnl
        model.balance += pnl

        # Update counts
        model.total_bets += 1
        if is_win:
            model.win_count += 1
        else:
            model.loss_count += 1

        # Recalculate ROI
        if model.initial_balance > 0:
            model.roi_percentage = (
                model.total_pnl / model.initial_balance * 100
            )

        # Check if eliminated
        if model.balance <= 0:
            model.balance = Decimal("0.00")
            model.is_active = False
            logger.warning(f"Model {model.name} eliminated (balance: $0)")

        await db.commit()
        await db.refresh(model)
        return model

    async def record_abstain(self, db: AsyncSession, model_id: UUID) -> AIModel:
        """Record that a model abstained from betting."""
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        model.abstain_count += 1
        await db.commit()
        await db.refresh(model)
        return model

    async def get_leaderboard(self, db: AsyncSession) -> list[AIModel]:
        """Get models ranked by ROI percentage."""
        result = await db.execute(
            select(AIModel)
            .order_by(AIModel.roi_percentage.desc())
        )
        return list(result.scalars().all())

    async def reset_model_balance(
        self,
        db: AsyncSession,
        model_id: UUID,
        new_balance: Decimal,
    ) -> AIModel:
        """Reset a model's balance (admin function)."""
        model = await self.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        model.balance = new_balance
        model.is_active = True
        await db.commit()
        await db.refresh(model)
        logger.info(f"Reset model {model.name} balance to ${new_balance}")
        return model


# Singleton instance
ai_model_service = AIModelService()
