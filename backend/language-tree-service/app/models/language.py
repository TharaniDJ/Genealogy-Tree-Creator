from pydantic import BaseModel
from typing import List, Optional

class LanguageRelationship(BaseModel):
    """Model for language relationships"""
    language1: str
    relationship: str
    language2: str
    language1_qid: Optional[str] = None
    language2_qid: Optional[str] = None

class DistributionMapResponse(BaseModel):
    """Model for distribution map image response"""
    qid: str
    image_url: Optional[str] = None
    found: bool

class LanguageTreeData(BaseModel):
    """Model for complete language tree data"""
    relationships: List[LanguageRelationship]
    total_relationships: int
    depth: int
    root_language: str

class LanguageInfo(BaseModel):
    """Model for detailed language information"""
    speakers: Optional[str] = None
    iso_code: Optional[str] = None
    distribution_map_url: Optional[str] = None

class UserInput(BaseModel):
    """Model for user input"""
    language_name: str
    depth: int
    user_id: Optional[str] = None  # Optional field to track user sessions

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str  # "relationship", "language_info", "status", "error"
    data: dict
