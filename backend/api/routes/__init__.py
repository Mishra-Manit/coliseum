"""API routes module."""

from api.routes.admin import router as admin_router
from api.routes.events import router as events_router
from api.routes.leaderboard import router as leaderboard_router
from api.routes.models import router as models_router
from api.routes.sessions import router as sessions_router
from api.routes.websocket import router as websocket_router

__all__ = [
    "admin_router",
    "events_router",
    "leaderboard_router",
    "models_router",
    "sessions_router",
    "websocket_router",
]
