from typing import Dict
from fastapi import WebSocket, APIRouter
from mvp.search.session import SearchSession
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"WS Connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"WS Disconnected: {session_id}")

    async def send_update(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Error sending WS message to {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()

router = APIRouter()

@router.websocket("/ws/search/{session_id}")
async def search_progress(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive, maybe wait for client messages if needed
            # For now just receiving is enough to keep it open
            await websocket.receive_text()
    except Exception:
        manager.disconnect(session_id)
