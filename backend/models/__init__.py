"""Database models module (Beanie/MongoDB)."""

from typing import List, Type

from beanie import Document

from models.ai_model import AIModel
from models.bet import Bet
from models.betting_session import BettingSession
from models.daily_leaderboard import DailyLeaderboard
from models.event import Event
from models.event_summary import EventSummary
from models.session_message import SessionMessage
from models.settlement import Settlement


def get_document_models() -> List[Type[Document]]:
    """
    Return all Beanie document models for registration with init_beanie().

    This function is called by database/connection.py during app startup
    to register all document models with Beanie ODM.
    """
    return [
        AIModel,
        Bet,
        BettingSession,
        DailyLeaderboard,
        Event,
        EventSummary,
        SessionMessage,
        Settlement,
    ]


__all__ = [
    # Models
    "AIModel",
    "Bet",
    "BettingSession",
    "DailyLeaderboard",
    "Event",
    "EventSummary",
    "SessionMessage",
    "Settlement",
    # Utilities
    "get_document_models",
]
