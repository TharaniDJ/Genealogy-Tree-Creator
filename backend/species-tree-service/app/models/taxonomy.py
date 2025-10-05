"""
Pydantic models for taxonomic data structures
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from datetime import datetime

class TaxonomicRank(BaseModel):
    """Represents a taxonomic rank with its name and optional link"""
    rank: str
    name: str
    link: Optional[str] = None

class TaxonomyResponse(BaseModel):
    """Response model for taxonomy extraction"""
    input_scientific_name: str
    genus: str
    source_url: str
    ancestral_taxa: List[TaxonomicRank]
    total_taxa_found: int
    extraction_timestamp: str
    extraction_method: str = "real-time"

class TaxonomicTuple(BaseModel):
    """Represents a taxonomic relationship as a tuple"""
    parent_taxon: str = Field(..., description="The parent taxonomic entity")
    has_child: bool = Field(..., description="Whether this parent has children")
    child_taxon: str = Field(..., description="The child taxonomic entity")

class TaxonomyTuplesResponse(BaseModel):
    """Response containing taxonomic relationships as tuples"""
    scientific_name: str
    tuples: List[TaxonomicTuple]
    total_relationships: int
    extraction_method: str = "real-time"

class ExpansionRequest(BaseModel):
    """Request model for taxonomic expansion"""
    taxon_name: str = Field(..., description="Name of the taxon to expand from")
    rank: str = Field(..., description="Taxonomic rank of the starting taxon")
    target_rank: Optional[str] = Field(None, description="Target rank to expand to (if specified)")

class ExpansionResponse(BaseModel):
    """Response model for taxonomic expansion"""
    parent_taxon: str
    parent_rank: str
    children: List[str]
    child_rank: str
    tuples: List[TaxonomicTuple]
    total_children: int

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    status_code: int