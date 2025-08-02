from pydantic import BaseModel
from typing import Dict, Any

class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]
    user_id: str = None
