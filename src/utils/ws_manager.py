from fastapi import WebSocket
from typing import Dict, List

class WebSocketConnectionManager:
    #A constructor function that maps ACTIVE or INACTIVE staff_ids to a list of active connections
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    ###########################################################################################
    #A function to connect an ACTIVE staff_id to websocket for real time update
    async def connect(self, staff_id: int, websocket: WebSocket):
        await websocket.accept()

        #Check if a staff_id is active
        if staff_id not in self.active_connections:
            self.active_connections[staff_id] = []

        #Add to connection
        self.active_connections[staff_id].append(websocket)

    ###########################################################################################
    #A function to disconnect or disable an ACTIVE staff_id from websocket
    def disconnect(self, staff_id: int, websocket: WebSocket):
        #Check if a staff_id is active and then disable connection
        if staff_id in self.active_connections:
            self.active_connections[staff_id].remove(websocket)

            #Check if a staff_id is inactive and then remove staff_id
            if not self.active_connections[staff_id]:
                del self.active_connections[staff_id]

    ###########################################################################################
    #A function to diistribute or show the connection
    async def broadcast(self, payload: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

ws_manager = WebSocketConnectionManager()

    
