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
        # Create a Redis pub-sub client
        pubsub = redis_client.pubsub()

        # Subscribe the client to a channel; foodhub_ws_channel
        await pubsub.subscribe("foodhub_ws_channel")
        try:
            # Allow client to listen to all changes/messages happening eg. deadline changes
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])

                    # When a message is recieved, broadcast to all servers or workers ( local WebSocket connections)
                    await self._local_broadcast(payload)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("foodhub_ws_channel")

    ###########################################################################################
    #A function to connect an ACTIVE staff_id to websocket for real time update
    async def connect(self, staff_id: int, websocket: WebSocket):
        # Accept websocket connection
        await websocket.accept()

        #Check if a staff_id is active
        if staff_id not in self.active_connections:
            self.active_connections[staff_id] = []

        # Add connection to a tracking dictionary
        self.active_connections[staff_id].append(websocket)

        # Start the background Pub/Sub subscription task on the first connection (Lazy initialization)
        if self.pubsub_task is None or self.pubsub_task.done():
            self.pubsub_task = asyncio.create_task(self.start_listener())

    ###########################################################################################
    #A function to disconnect or disable an ACTIVE staff_id from websocket
    def disconnect(self, staff_id: int, websocket: WebSocket):
        # Check if a staff_id is active and then disable connection
        # Remove accepted connection from the tracking dictionary
        if staff_id in self.active_connections:
            self.active_connections[staff_id].remove(websocket)

            # Check if a staff_id is inactive or has no connection and then remove staff_id
            if not self.active_connections[staff_id]:
                del self.active_connections[staff_id]

            # NB: It doesn't stop the pub-sub listener (it keeps running even if all clients disconnect).

    ###########################################################################################
    #A function to distribute or show the connection and broadcast to connections on this server worker only
    async def _local_broadcast(self, payload: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    ###########################################################################################
    # Publish to Redis Pub/Sub client so ALL backend servers receive it and broadcast locally
    async def broadcast(self, payload: dict):
        try:
            # Send published changes or messages from channel, foodhub_ws_channel TO 
            # all subscribed instances on the same channel i.e broadcast
            await redis_client.publish("foodhub_ws_channel", json.dumps(payload))
        except Exception:
            # Fallback: if Redis is offline, broadcast to local clients directly
            await self._local_broadcast(payload)

ws_manager = WebSocketConnectionManager()

    
