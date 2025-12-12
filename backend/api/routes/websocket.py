"""WebSocket API routes."""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import websocket_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.

    Client sends:
    - {"action": "subscribe", "event_id": "uuid"}
    - {"action": "unsubscribe", "event_id": "uuid"}

    Server sends:
    - {"type": "price_update", "event_id": "uuid", "price": 0.52, "timestamp": "..."}
    - {"type": "message", "event_id": "uuid", "session_id": "uuid", "data": {...}}
    - {"type": "bet", "event_id": "uuid", "data": {...}}
    - {"type": "settlement", "event_id": "uuid", "data": {...}}
    - {"type": "viewers", "event_id": "uuid", "count": 15402, "timestamp": "..."}
    - {"type": "session_status", "event_id": "uuid", "session_id": "uuid", ...}
    - {"type": "error", "message": "...", "code": "..."}
    """
    await websocket_service.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                event_id = message.get("event_id")

                if not action or not event_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing action or event_id",
                        "code": "INVALID_MESSAGE",
                    })
                    continue

                try:
                    event_uuid = UUID(event_id)
                except ValueError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid event_id format",
                        "code": "INVALID_UUID",
                    })
                    continue

                if action == "subscribe":
                    websocket_service.subscribe_to_event(websocket, event_uuid)
                    await websocket.send_json({
                        "type": "subscribed",
                        "event_id": event_id,
                    })
                    logger.debug(f"Client subscribed to event {event_id}")

                elif action == "unsubscribe":
                    websocket_service.unsubscribe_from_event(websocket, event_uuid)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "event_id": event_id,
                    })
                    logger.debug(f"Client unsubscribed from event {event_id}")

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}",
                        "code": "UNKNOWN_ACTION",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "code": "INVALID_JSON",
                })

    except WebSocketDisconnect:
        websocket_service.disconnect(websocket)
        logger.debug("WebSocket disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_service.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    from services.websocket_service import manager

    return {
        "total_connections": manager.get_total_connections(),
        "subscriptions": {
            str(event_id): len(subs)
            for event_id, subs in manager.event_subscriptions.items()
        },
    }
