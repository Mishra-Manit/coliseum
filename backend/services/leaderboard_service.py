"""Leaderboard calculations and snapshots service."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AIModel, Bet, DailyLeaderboard

logger = logging.getLogger(__name__)


class LeaderboardService:
    """
    Rankings and daily performance snapshots.
    """

    async def get_current_leaderboard(
        self, db: AsyncSession
    ) -> list[dict]:
        """
        Get current overall leaderboard ranked by ROI.
        """
        result = await db.execute(
            select(AIModel)
            .order_by(AIModel.roi_percentage.desc())
        )
        models = list(result.scalars().all())

        leaderboard = []
        for rank, model in enumerate(models, 1):
            leaderboard.append({
                "rank": rank,
                "model": {
                    "id": model.id,
                    "external_id": model.external_id,
                    "name": model.name,
                    "color": model.color,
                    "text_color": model.text_color,
                    "avatar": model.avatar,
                    "balance": model.balance,
                },
                "total_pnl": model.total_pnl,
                "roi_percentage": model.roi_percentage,
                "win_count": model.win_count,
                "loss_count": model.loss_count,
                "is_active": model.is_active,
            })

        return leaderboard

    async def get_daily_leaderboard(
        self,
        db: AsyncSession,
        target_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Get leaderboard for a specific day.
        """
        if target_date is None:
            target_date = date.today()

        result = await db.execute(
            select(DailyLeaderboard)
            .where(DailyLeaderboard.date == target_date)
            .order_by(DailyLeaderboard.rank)
        )
        entries = list(result.scalars().all())

        if not entries:
            # Fall back to current leaderboard
            return await self.get_current_leaderboard(db)

        # Fetch model details
        model_ids = [e.model_id for e in entries]
        models_result = await db.execute(
            select(AIModel).where(AIModel.id.in_(model_ids))
        )
        models_map = {m.id: m for m in models_result.scalars().all()}

        leaderboard = []
        for entry in entries:
            model = models_map.get(entry.model_id)
            if model:
                leaderboard.append({
                    "rank": entry.rank,
                    "model": {
                        "id": model.id,
                        "external_id": model.external_id,
                        "name": model.name,
                        "color": model.color,
                        "text_color": model.text_color,
                        "avatar": model.avatar,
                        "balance": entry.total_balance,
                    },
                    "daily_pnl": entry.daily_pnl,
                    "daily_bets": entry.daily_bets,
                    "daily_wins": entry.daily_wins,
                    "daily_losses": entry.daily_losses,
                    "total_pnl": entry.total_pnl,
                    "total_roi": entry.total_roi,
                })

        return leaderboard

    async def update_daily_snapshot(
        self,
        db: AsyncSession,
        target_date: Optional[date] = None,
    ) -> list[DailyLeaderboard]:
        """
        Record daily performance snapshot for all models.
        """
        if target_date is None:
            target_date = date.today()

        # Get all models ranked by ROI
        result = await db.execute(
            select(AIModel).order_by(AIModel.roi_percentage.desc())
        )
        models = list(result.scalars().all())

        # Calculate daily stats for each model
        snapshots = []
        for rank, model in enumerate(models, 1):
            # Get daily bets
            daily_stats = await self._calculate_daily_stats(
                db, model.id, target_date
            )

            # Check if snapshot exists
            existing = await db.execute(
                select(DailyLeaderboard)
                .where(DailyLeaderboard.model_id == model.id)
                .where(DailyLeaderboard.date == target_date)
            )
            snapshot = existing.scalar_one_or_none()

            if snapshot:
                # Update existing
                snapshot.rank = rank
                snapshot.daily_pnl = daily_stats["daily_pnl"]
                snapshot.daily_bets = daily_stats["daily_bets"]
                snapshot.daily_wins = daily_stats["daily_wins"]
                snapshot.daily_losses = daily_stats["daily_losses"]
                snapshot.total_balance = model.balance
                snapshot.total_pnl = model.total_pnl
                snapshot.total_roi = model.roi_percentage
            else:
                # Create new
                snapshot = DailyLeaderboard(
                    model_id=model.id,
                    date=target_date,
                    rank=rank,
                    daily_pnl=daily_stats["daily_pnl"],
                    daily_bets=daily_stats["daily_bets"],
                    daily_wins=daily_stats["daily_wins"],
                    daily_losses=daily_stats["daily_losses"],
                    total_balance=model.balance,
                    total_pnl=model.total_pnl,
                    total_roi=model.roi_percentage,
                )
                db.add(snapshot)

            snapshots.append(snapshot)

        await db.commit()
        logger.info(f"Updated daily leaderboard for {target_date}")
        return snapshots

    async def _calculate_daily_stats(
        self,
        db: AsyncSession,
        model_id: UUID,
        target_date: date,
    ) -> dict:
        """Calculate daily statistics for a model."""
        # Get bets settled today
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        result = await db.execute(
            select(Bet)
            .where(Bet.model_id == model_id)
            .where(Bet.settled == True)
            .where(Bet.settled_at >= start_of_day)
            .where(Bet.settled_at <= end_of_day)
        )
        bets = list(result.scalars().all())

        daily_pnl = sum(b.pnl or Decimal("0") for b in bets)
        daily_wins = sum(1 for b in bets if b.pnl and b.pnl > 0)
        daily_losses = sum(1 for b in bets if b.pnl and b.pnl < 0)

        return {
            "daily_pnl": daily_pnl,
            "daily_bets": len(bets),
            "daily_wins": daily_wins,
            "daily_losses": daily_losses,
        }

    async def get_leaderboard_history(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> list[dict]:
        """
        Get historical leaderboard data for the past N days.
        """
        from datetime import timedelta

        today = date.today()
        history = []

        for i in range(days):
            target_date = today - timedelta(days=i)
            daily = await self.get_daily_leaderboard(db, target_date)
            history.append({
                "date": target_date.isoformat(),
                "leaderboard": daily,
            })

        return history

    async def get_model_ranking_history(
        self,
        db: AsyncSession,
        model_id: UUID,
        days: int = 30,
    ) -> list[dict]:
        """
        Get ranking history for a specific model.
        """
        from datetime import timedelta

        today = date.today()
        start_date = today - timedelta(days=days)

        result = await db.execute(
            select(DailyLeaderboard)
            .where(DailyLeaderboard.model_id == model_id)
            .where(DailyLeaderboard.date >= start_date)
            .order_by(DailyLeaderboard.date)
        )
        entries = list(result.scalars().all())

        return [
            {
                "date": e.date.isoformat(),
                "rank": e.rank,
                "balance": float(e.total_balance),
                "pnl": float(e.total_pnl),
                "roi": float(e.total_roi),
            }
            for e in entries
        ]


# Singleton instance
leaderboard_service = LeaderboardService()
