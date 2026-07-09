import asyncio
from src.utils.redis import redis_client
from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketConnectionManager:
    # Constructor mapping active staff_ids to their websocket connections
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

        self.pubsub_task: asyncio.Task | None = None

    ###########################################################################################
    # Background task to listen to Redis Pub/Sub events and distribute to local clients
    async def start_listener(self):
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("foodhub_ws_channel")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await self._local_broadcast(payload)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("foodhub_ws_channel")

    ###########################################################################################
    #A function to connect an ACTIVE staff_id to websocket for real time update
    async def connect(self, staff_id: int, websocket: WebSocket):
        await websocket.accept()

        #Check if a staff_id is active
        if staff_id not in self.active_connections:
            self.active_connections[staff_id] = []

        #Add to connection
        self.active_connections[staff_id].append(websocket)

        # Start the background Pub/Sub subscription task on the first connection
        if self.pubsub_task is None or self.pubsub_task.done():
            self.pubsub_task = asyncio.create_task(self.start_listener())

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
    #A function to distribute or show the connection and brroadcast to connections on this server worker only
    async def _local_broadcast(self, payload: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    ###########################################################################################
    # Publish to Redis Pub/Sub so ALL backend instances receive it and broadcast locally
    async def broadcast(self, payload: dict):
        try:
            await redis_client.publish("foodhub_ws_channel", json.dumps(payload))
        except Exception:
            # Fallback: if Redis is offline, broadcast to local clients directly
            await self._local_broadcast(payload)

ws_manager = WebSocketConnectionManager()

    
