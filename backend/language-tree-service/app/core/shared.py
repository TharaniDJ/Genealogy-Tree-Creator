"""Shared instances across the application"""

from app.core.websocket_manager import WebSocketManager

# Create a shared websocket manager instance
websocket_manager = WebSocketManager()