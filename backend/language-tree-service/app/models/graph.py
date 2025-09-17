from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.language import LanguageRelationship


class GraphSaveRequest(BaseModel):
    user_id: Optional[str] = Field(default="1234", description="User ID, defaults to 1234")
    name: str = Field(description="Graph name (defaults to search name on client)")
    depth: int = Field(ge=1, le=5)
    node_count: int = Field(ge=0)
    relationships: List[LanguageRelationship]


class GraphResponse(BaseModel):
    id: str
    user_id: str
    name: str
    depth: int
    node_count: int
    relationships: List[LanguageRelationship]
    created_at: datetime
    updated_at: datetime


class GraphUpdateRequest(BaseModel):
    name: Optional[str] = None
    depth: Optional[int] = Field(default=None, ge=1, le=5)
    node_count: Optional[int] = Field(default=None, ge=0)
    relationships: Optional[List[LanguageRelationship]] = None
