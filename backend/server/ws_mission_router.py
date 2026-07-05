import asyncio
import json
import uuid
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import structlog

logger = structlog.get_logger("mission_ws")

ws_mission_router = APIRouter(prefix="/ws/missions", tags=["Mission Websockets"])

class ConnectionManager:
    def __init__(self):
        # tenant_id -> list of active websockets
        self.active_connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        logger.info("ws_client_connected", tenant_id=tenant_id)

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            if websocket in self.active_connections[tenant_id]:
                self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info("ws_client_disconnected", tenant_id=tenant_id)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        if tenant_id in self.active_connections:
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("ws_broadcast_failed", error=str(e))

manager = ConnectionManager()

@ws_mission_router.websocket("/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive, listen for client pings if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)

async def dispatch_mission_event_to_ui(tenant_id: str, event_data: dict):
    """
    Called by the Mission Event Bus to push real-time telemetry to the Command Center UI.
    Formats the raw DB event into a structured Phase 5 UI Event.
    """
    ui_event = {
        "event_id": str(uuid.uuid4()),
        "correlation_id": event_data.get("task_id", "system"),
        "mission_id": event_data.get("mission_id"),
        "timestamp": event_data.get("created_at"),
        "severity": "info",
        "category": "mission_update",
        "payload": event_data
    }
    
    # Send Notification (Stub for Phase 5 rule engine)
    if event_data.get("event_type") == "mission_completed":
        logger.info("triggering_notification", type="mission_completed", tenant=tenant_id)
        
    await manager.broadcast_to_tenant(tenant_id, ui_event)
