from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class GraphBase(BaseModel):
    graph_name: str = Field(..., min_length=1, max_length=200)
    graph_type: str = Field(..., pattern="^(species|language|family)$")
    depth_usage: bool = Field(default=False)
    depth: Optional[int] = Field(default=None, ge=1, le=10)
    graph_data: List[Dict[str, Any]] = Field(...)
    description: Optional[str] = Field(default=None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "graph_name": "Indo-European Language Family",
                "graph_type": "language",
                "depth_usage": True,
                "depth": 3,
                "graph_data": [
                    {
                        "language1": "English",
                        "relationship": "Child of",
                        "language2": "Proto-Germanic",
                        "language1_qid": "Q1860",
                        "language2_qid": "Q21125",
                        "language1_category": "language",
                        "language2_category": "proto_language"
                    }
                ],
                "description": "A comprehensive tree of Indo-European languages"
            }
        }
    }


class GraphCreate(GraphBase):
    pass


class GraphUpdate(BaseModel):
    graph_name: Optional[str] = Field(None, min_length=1, max_length=200)
    depth_usage: Optional[bool] = None
    depth: Optional[int] = Field(None, ge=1, le=10)
    graph_data: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = Field(None, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "graph_name": "Updated Graph Name",
                "description": "Updated description"
            }
        }
    }


class GraphInDB(GraphBase):
    """Internal model for database operations - not used in API responses"""
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True
    }


class GraphOut(BaseModel):
    id: str
    user_id: str
    graph_name: str
    graph_type: str
    depth_usage: bool
    depth: Optional[int]
    graph_data: List[Dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "user_id": "507f191e810c19729de860ea",
                "graph_name": "Indo-European Language Family",
                "graph_type": "language",
                "depth_usage": True,
                "depth": 3,
                "graph_data": [
                    {
                        "language1": "English",
                        "relationship": "Child of",
                        "language2": "Proto-Germanic"
                    }
                ],
                "description": "A comprehensive tree of Indo-European languages",
                "created_at": "2025-10-17T10:30:00Z",
                "updated_at": "2025-10-17T10:30:00Z"
            }
        }
    }


class GraphListItem(BaseModel):
    """Simplified graph info for list endpoints"""
    id: str
    graph_name: str
    graph_type: str
    depth_usage: bool
    depth: Optional[int]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    nodes_count: int  # Number of items in graph_data

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "graph_name": "Indo-European Language Family",
                "graph_type": "language",
                "depth_usage": True,
                "depth": 3,
                "description": "A comprehensive tree of Indo-European languages",
                "created_at": "2025-10-17T10:30:00Z",
                "updated_at": "2025-10-17T10:30:00Z",
                "nodes_count": 45
            }
        }
    }
