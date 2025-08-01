from pydantic import BaseModel
from typing import List, Optional

class TaxonomicRelationship(BaseModel):
    """Model for taxonomic relationships"""
    entity1: str
    relationship: str
    entity2: str

class SpeciesTreeData(BaseModel):
    """Model for complete species tree data"""
    relationships: List[TaxonomicRelationship]
    total_relationships: int
    depth: int
    root_species: str

class SpeciesInfo(BaseModel):
    """Model for detailed species information"""
    name: str
    scientific_name: Optional[str] = None
    common_names: Optional[List[str]] = None
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    conservation_status: Optional[str] = None
    habitat: Optional[str] = None
    distribution: Optional[str] = None
    diet: Optional[str] = None
    size: Optional[str] = None
    lifespan: Optional[str] = None
    image_url: Optional[str] = None

class TaxonomicClassification(BaseModel):
    """Model for complete taxonomic classification"""
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None

class UserInput(BaseModel):
    """Model for user input"""
    species_name: str
    depth: int
    user_id: Optional[str] = None  # Optional field to track user sessions

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str  # "relationship", "species_info", "status", "error"
    data: dict
