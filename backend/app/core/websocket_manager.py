from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        """Send a message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

    async def broadcast_relationships(self, relationships: List[str]):
        """Send a list of relationships to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(relationships)
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

    async def send_relationship(self, relationship: dict):
        """Send a single relationship to all connected clients"""
        message = json.dumps({
            "type": "relationship",
            "data": relationship
        })
        await self.send_message(message)

    async def send_status(self, status: str, progress: int = 0):
        """Send status update to all connected clients"""
        message = json.dumps({
            "type": "status",
            "data": {"message": status, "progress": progress}
        })
        await self.send_message(message)