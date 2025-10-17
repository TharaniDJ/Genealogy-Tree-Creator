from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.graph import GraphCreate, GraphOut, GraphUpdate, GraphListItem
from app.api import graph_crud
from app.core.auth import get_current_user
from typing import List, Optional
import logging
from bson.objectid import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)


def format_graph_out(doc: dict) -> GraphOut:
    """Convert MongoDB document to GraphOut schema"""
    return GraphOut(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        graph_name=doc["graph_name"],
        graph_type=doc["graph_type"],
        depth_usage=doc["depth_usage"],
        depth=doc.get("depth"),
        graph_data=doc["graph_data"],
        description=doc.get("description"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )


def format_graph_list_item(doc: dict) -> GraphListItem:
    """Convert MongoDB document to GraphListItem schema"""
    return GraphListItem(
        id=str(doc["_id"]),
        graph_name=doc["graph_name"],
        graph_type=doc["graph_type"],
        depth_usage=doc["depth_usage"],
        depth=doc.get("depth"),
        description=doc.get("description"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        nodes_count=len(doc.get("graph_data", []))
    )


@router.post('/graphs', response_model=GraphOut, status_code=status.HTTP_201_CREATED)
async def create_graph(
    graph_in: GraphCreate,
    current_user=Depends(get_current_user)
):
    """
    Create a new graph for the authenticated user.
    
    - **graph_name**: Unique name for the graph (per type)
    - **graph_type**: Type of graph (species, language, family)
    - **depth_usage**: Whether depth was used in graph generation
    - **depth**: Depth value if depth_usage is true
    - **graph_data**: List of relationships/tuples (structure varies by type)
    - **description**: Optional description
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Creating graph '{graph_in.graph_name}' for user {user_id}")
        
        # Validate depth field
        if graph_in.depth_usage and graph_in.depth is None:
            raise HTTPException(
                status_code=400,
                detail="Depth value is required when depth_usage is true"
            )
        
        # Validate graph_data is not empty
        if not graph_in.graph_data or len(graph_in.graph_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="graph_data cannot be empty"
            )
        
        # Create graph
        graph_doc = await graph_crud.create_graph(
            user_id=user_id,
            graph_data=graph_in.model_dump()
        )
        
        logger.info(f"Graph created successfully: {graph_doc['_id']}")
        return format_graph_out(graph_doc)
        
    except ValueError as ve:
        # Handle duplicate name error
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create graph: {str(e)}"
        )


@router.get('/graphs', response_model=List[GraphListItem])
async def list_graphs(
    graph_type: Optional[str] = Query(None, description="Filter by graph type (species, language, family)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    current_user=Depends(get_current_user)
):
    """
    Get all graphs for the authenticated user.
    
    - **graph_type**: Optional filter by type (species, language, family)
    - **skip**: Pagination offset
    - **limit**: Maximum results per page
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Fetching graphs for user {user_id}, type={graph_type}")
        
        # Validate graph_type if provided
        if graph_type and graph_type not in ["species", "language", "family"]:
            raise HTTPException(
                status_code=400,
                detail="graph_type must be one of: species, language, family"
            )
        
        graphs = await graph_crud.get_user_graphs(
            user_id=user_id,
            graph_type=graph_type,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Found {len(graphs)} graphs for user {user_id}")
        return [format_graph_list_item(g) for g in graphs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing graphs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list graphs: {str(e)}"
        )


@router.get('/graphs/{graph_id}', response_model=GraphOut)
async def get_graph(
    graph_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get a specific graph by ID.
    
    - **graph_id**: The unique identifier of the graph
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Fetching graph {graph_id} for user {user_id}")
        
        # Validate ObjectId format
        if not ObjectId.is_valid(graph_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid graph ID format"
            )
        
        graph = await graph_crud.get_graph_by_id(graph_id=graph_id, user_id=user_id)
        
        if not graph:
            logger.warning(f"Graph {graph_id} not found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="Graph not found"
            )
        
        logger.info(f"Graph {graph_id} retrieved successfully")
        return format_graph_out(graph)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph: {str(e)}"
        )


@router.put('/graphs/{graph_id}', response_model=GraphOut)
async def update_graph(
    graph_id: str,
    graph_update: GraphUpdate,
    current_user=Depends(get_current_user)
):
    """
    Update a graph. Only provided fields will be updated.
    
    - **graph_id**: The unique identifier of the graph
    - **graph_name**: New name (optional)
    - **depth_usage**: Update depth usage flag (optional)
    - **depth**: Update depth value (optional)
    - **graph_data**: Update graph data (optional)
    - **description**: Update description (optional)
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Updating graph {graph_id} for user {user_id}")
        
        # Validate ObjectId format
        if not ObjectId.is_valid(graph_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid graph ID format"
            )
        
        # Only include non-None fields in update
        update_data = graph_update.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )
        
        # Validate depth logic
        if "depth_usage" in update_data and update_data["depth_usage"] and "depth" not in update_data:
            # Check if existing graph has depth
            existing = await graph_crud.get_graph_by_id(graph_id, user_id)
            if existing and not existing.get("depth"):
                raise HTTPException(
                    status_code=400,
                    detail="Depth value is required when depth_usage is true"
                )
        
        # Validate graph_data if provided
        if "graph_data" in update_data and (not update_data["graph_data"] or len(update_data["graph_data"]) == 0):
            raise HTTPException(
                status_code=400,
                detail="graph_data cannot be empty"
            )
        
        updated_graph = await graph_crud.update_graph(
            graph_id=graph_id,
            user_id=user_id,
            update_data=update_data
        )
        
        if not updated_graph:
            logger.warning(f"Graph {graph_id} not found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="Graph not found"
            )
        
        logger.info(f"Graph {graph_id} updated successfully")
        return format_graph_out(updated_graph)
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update graph: {str(e)}"
        )


@router.delete('/graphs/{graph_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(
    graph_id: str,
    current_user=Depends(get_current_user)
):
    """
    Delete a graph.
    
    - **graph_id**: The unique identifier of the graph
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Deleting graph {graph_id} for user {user_id}")
        
        # Validate ObjectId format
        if not ObjectId.is_valid(graph_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid graph ID format"
            )
        
        deleted = await graph_crud.delete_graph(graph_id=graph_id, user_id=user_id)
        
        if not deleted:
            logger.warning(f"Graph {graph_id} not found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="Graph not found"
            )
        
        logger.info(f"Graph {graph_id} deleted successfully")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete graph: {str(e)}"
        )


@router.get('/graphs/stats/count')
async def get_graph_stats(
    graph_type: Optional[str] = Query(None, description="Filter by graph type"),
    current_user=Depends(get_current_user)
):
    """
    Get statistics about user's graphs.
    
    - **graph_type**: Optional filter by type
    """
    try:
        user_id = current_user["id"]
        
        # Validate graph_type if provided
        if graph_type and graph_type not in ["species", "language", "family"]:
            raise HTTPException(
                status_code=400,
                detail="graph_type must be one of: species, language, family"
            )
        
        total = await graph_crud.count_user_graphs(user_id=user_id, graph_type=graph_type)
        
        # If no type filter, get counts by type
        if not graph_type:
            species_count = await graph_crud.count_user_graphs(user_id=user_id, graph_type="species")
            language_count = await graph_crud.count_user_graphs(user_id=user_id, graph_type="language")
            family_count = await graph_crud.count_user_graphs(user_id=user_id, graph_type="family")
            
            return {
                "total": total,
                "by_type": {
                    "species": species_count,
                    "language": language_count,
                    "family": family_count
                }
            }
        
        return {"total": total, "graph_type": graph_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph stats: {str(e)}"
        )
