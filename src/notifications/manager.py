from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Maps staff_id -> list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, staff_id: int, websocket: WebSocket):
        await websocket.accept()
        if staff_id not in self.active_connections:
            self.active_connections[staff_id] = []
        self.active_connections[staff_id].append(websocket)

    def disconnect(self, staff_id: int, websocket: WebSocket):
        if staff_id in self.active_connections:
            self.active_connections[staff_id].remove(websocket)
            if not self.active_connections[staff_id]:
                del self.active_connections[staff_id]

    async def send_private_payload(self, staff_id: int, payload: dict):
        if staff_id in self.active_connections:
            for connection in self.active_connections[staff_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    async def broadcast(self, payload: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

manager = ConnectionManager()