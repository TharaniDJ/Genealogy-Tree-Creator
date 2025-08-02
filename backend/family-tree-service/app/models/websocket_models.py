from pydantic import BaseModel
from typing import List, Optional

class Relationship(BaseModel):
    entity1: str
    relationship: str
    entity2: str

class WebSocketMessage(BaseModel):
    action: str
    data: Optional[List[Relationship]] = None
    error: Optional[str] = None

class WebSocketConnection(BaseModel):
    client_id: str
    connection_id: str