from pydantic import BaseModel
from typing import List, Optional

class Relationship(BaseModel):
    entity1: str
    relationship: str
    entity2: str

class GenealogyData(BaseModel):
    relationships: List[Relationship]
    total_relationships: int
    depth: int
    page_title: str

class UserInput(BaseModel):
    page_title: str
    depth: int
    user_id: Optional[str] = None  # Optional field to track user sessions or requests