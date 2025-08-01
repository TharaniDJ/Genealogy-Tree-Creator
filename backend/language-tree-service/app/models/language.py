from pydantic import BaseModel
from typing import List, Optional

class LanguageRelationship(BaseModel):
    """Model for language relationships"""
    entity1: str
    relationship: str
    entity2: str

class LanguageTreeData(BaseModel):
    """Model for complete language tree data"""
    relationships: List[LanguageRelationship]
    total_relationships: int
    depth: int
    root_language: str

class LanguageInfo(BaseModel):
    """Model for detailed language information"""
    name: str
    language_family: Optional[str] = None
    speakers: Optional[str] = None
    writing_system: Optional[str] = None
    iso_code: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None  # e.g., "living", "extinct", "constructed"
    image_url: Optional[str] = None

class UserInput(BaseModel):
    """Model for user input"""
    language_name: str
    depth: int
    user_id: Optional[str] = None  # Optional field to track user sessions

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str  # "relationship", "language_info", "status", "error"
    data: dict
