import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket connection manager for species tree service"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
        logger.info(f"WebSocket connected: {connection_id} for user: {user_id}")
        
    def disconnect(self, connection_id: str, user_id: str = None):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                
        logger.info(f"WebSocket disconnected: {connection_id} for user: {user_id}")
        
    async def send_personal_message(self, message: str, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
                
    async def send_to_user(self, message: str, user_id: str):
        """Send a message to all connections of a specific user"""
        if user_id in self.user_connections:
            connection_ids = self.user_connections[user_id].copy()
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)
                
    async def broadcast(self, message: str):
        """Send a message to all active connections"""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)
            
    async def send_message(self, message: str, connection_id: str = None):
        """Send message to specific connection or broadcast to all"""
        if connection_id:
            await self.send_personal_message(message, connection_id)
        else:
            await self.broadcast(message)
            
    async def send_json(self, data: dict, connection_id: str = None):
        """Send JSON data to connection(s)"""
        message = json.dumps(data)
        await self.send_message(message, connection_id)
        
    async def send_status(self, status: str, progress: int = None, connection_id: str = None):
        """Send status update"""
        data = {
            "type": "status",
            "data": {
                "message": status,
                "progress": progress
            }
        }
        await self.send_json(data, connection_id)
        
    async def send_error(self, error: str, connection_id: str = None):
        """Send error message"""
        data = {
            "type": "error",
            "data": {
                "message": error
            }
        }
        await self.send_json(data, connection_id)
        
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
        
    def get_user_count(self) -> int:
        """Get the number of unique users"""
        return len(self.user_connections)
