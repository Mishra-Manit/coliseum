"""WebSocket service for real-time updates."""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # All active connections
        self.active_connections: list[WebSocket] = []
        # Event subscriptions: event_id -> set of websockets
        self.event_subscriptions: dict[UUID, set[WebSocket]] = {}
        # Connection metadata
        self.connection_info: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(timezone.utc),
            "subscriptions": set(),
        }
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all event subscriptions
        info = self.connection_info.get(websocket, {})
        for event_id in info.get("subscriptions", set()):
            if event_id in self.event_subscriptions:
                self.event_subscriptions[event_id].discard(websocket)

        # Clean up connection info
        self.connection_info.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    def subscribe_to_event(self, websocket: WebSocket, event_id: UUID) -> None:
        """Subscribe a connection to event updates."""
        if event_id not in self.event_subscriptions:
            self.event_subscriptions[event_id] = set()
        self.event_subscriptions[event_id].add(websocket)

        # Track in connection info
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].add(event_id)

        logger.debug(f"Subscribed to event {event_id}")

    def unsubscribe_from_event(self, websocket: WebSocket, event_id: UUID) -> None:
        """Unsubscribe a connection from event updates."""
        if event_id in self.event_subscriptions:
            self.event_subscriptions[event_id].discard(websocket)

        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].discard(event_id)

        logger.debug(f"Unsubscribed from event {event_id}")

    async def broadcast_to_event(self, event_id: UUID, message: dict) -> None:
        """Broadcast message to all subscribers of an event."""
        subscribers = self.event_subscriptions.get(event_id, set())
        disconnected = []

        for websocket in subscribers:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_to_all(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []

        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws)

    def get_subscriber_count(self, event_id: UUID) -> int:
        """Get number of subscribers for an event."""
        return len(self.event_subscriptions.get(event_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)


# Singleton connection manager
manager = ConnectionManager()


class WebSocketService:
    """
    High-level WebSocket service for broadcasting updates.
    """

    def __init__(self):
        self.manager = manager

    async def connect(
        self, websocket: WebSocket, event_id: Optional[UUID] = None
    ) -> None:
        """Accept connection and optionally subscribe to event."""
        await self.manager.connect(websocket)
        if event_id:
            self.manager.subscribe_to_event(websocket, event_id)

    def disconnect(self, websocket: WebSocket) -> None:
        """Handle disconnection."""
        self.manager.disconnect(websocket)

    def subscribe_to_event(self, websocket: WebSocket, event_id: UUID) -> None:
        """Subscribe to event updates."""
        self.manager.subscribe_to_event(websocket, event_id)

    def unsubscribe_from_event(self, websocket: WebSocket, event_id: UUID) -> None:
        """Unsubscribe from event updates."""
        self.manager.unsubscribe_from_event(websocket, event_id)

    async def broadcast_price_update(
        self, event_id: UUID, price: Decimal
    ) -> None:
        """Broadcast price update to all event subscribers."""
        message = {
            "type": "price_update",
            "event_id": str(event_id),
            "price": float(price),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.manager.broadcast_to_event(event_id, message)

    async def broadcast_message(
        self,
        event_id: UUID,
        session_id: UUID,
        message_data: dict[str, Any],
    ) -> None:
        """Broadcast new AI reasoning message."""
        message = {
            "type": "message",
            "event_id": str(event_id),
            "session_id": str(session_id),
            "data": message_data,
        }
        await self.manager.broadcast_to_event(event_id, message)

    async def broadcast_bet(self, event_id: UUID, bet_data: dict[str, Any]) -> None:
        """Broadcast new bet placement."""
        message = {
            "type": "bet",
            "event_id": str(event_id),
            "data": bet_data,
        }
        await self.manager.broadcast_to_event(event_id, message)

    async def broadcast_settlement(
        self, event_id: UUID, settlement_data: dict[str, Any]
    ) -> None:
        """Broadcast event settlement."""
        message = {
            "type": "settlement",
            "event_id": str(event_id),
            "data": settlement_data,
        }
        await self.manager.broadcast_to_event(event_id, message)

    async def broadcast_viewer_count(self, event_id: UUID, count: int) -> None:
        """Broadcast viewer count update."""
        message = {
            "type": "viewers",
            "event_id": str(event_id),
            "count": count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.manager.broadcast_to_event(event_id, message)

    async def broadcast_session_status(
        self,
        event_id: UUID,
        session_id: UUID,
        model_id: UUID,
        status: str,
        final_position: Optional[str] = None,
    ) -> None:
        """Broadcast session status update."""
        message = {
            "type": "session_status",
            "event_id": str(event_id),
            "session_id": str(session_id),
            "model_id": str(model_id),
            "status": status,
            "final_position": final_position,
        }
        await self.manager.broadcast_to_event(event_id, message)

    def get_viewer_count(self, event_id: UUID) -> int:
        """Get simulated viewer count (subscribers + random offset)."""
        import random
        base = self.manager.get_subscriber_count(event_id)
        # Simulate more viewers than actual connections
        return base * random.randint(50, 150) + random.randint(100, 1000)


# Singleton instance
websocket_service = WebSocketService()
