from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from bson.objectid import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if not _client:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def graphs_collection():
    """Get the graphs collection"""
    return get_client()[settings.MONGO_DB].graphs


async def create_graph(user_id: str, graph_data: dict) -> dict:
    """
    Create a new graph for a user.
    
    Args:
        user_id: The user ID who owns the graph
        graph_data: Graph data containing name, type, depth info, and graph_data
        
    Returns:
        Created graph document with _id
        
    Raises:
        Exception: If graph with same name and type already exists for user
    """
    try:
        logger.info(f"Creating graph '{graph_data['graph_name']}' for user {user_id}")
        col = graphs_collection()
        
        # Check if graph with same name and type already exists for this user
        existing = await col.find_one({
            "user_id": user_id,
            "graph_name": graph_data["graph_name"],
            "graph_type": graph_data["graph_type"]
        })
        
        if existing:
            logger.warning(f"Graph '{graph_data['graph_name']}' of type '{graph_data['graph_type']}' already exists for user {user_id}")
            raise ValueError(f"A {graph_data['graph_type']} graph named '{graph_data['graph_name']}' already exists. Please use a different name.")
        
        # Create document
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "graph_name": graph_data["graph_name"],
            "graph_type": graph_data["graph_type"],
            "depth_usage": graph_data.get("depth_usage", False),
            "depth": graph_data.get("depth"),
            "graph_data": graph_data["graph_data"],
            "description": graph_data.get("description"),
            "created_at": now,
            "updated_at": now
        }
        
        logger.debug(f"Inserting graph document: {graph_data['graph_name']}")
        
        # Insert into database
        res = await col.insert_one(doc)
        doc["_id"] = res.inserted_id
        
        logger.info(f"Graph created successfully with ID: {res.inserted_id}")
        return doc
        
    except ValueError as ve:
        # Re-raise validation errors
        raise ve
    except Exception as e:
        logger.error(f"Error creating graph: {str(e)}")
        raise


async def get_graph_by_id(graph_id: str, user_id: str) -> Optional[dict]:
    """
    Get a specific graph by ID, ensuring it belongs to the user.
    
    Args:
        graph_id: The graph ID
        user_id: The user ID (for authorization)
        
    Returns:
        Graph document or None if not found
    """
    try:
        logger.debug(f"Looking up graph {graph_id} for user {user_id}")
        col = graphs_collection()
        doc = await col.find_one({
            "_id": ObjectId(graph_id),
            "user_id": user_id
        })
        return doc
    except Exception as e:
        logger.error(f"Error getting graph by ID: {str(e)}")
        raise


async def get_user_graphs(
    user_id: str, 
    graph_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[dict]:
    """
    Get all graphs for a user with optional filtering by type.
    
    Args:
        user_id: The user ID
        graph_type: Optional filter by graph type (species, language, family)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of graph documents
    """
    try:
        logger.debug(f"Fetching graphs for user {user_id}, type: {graph_type}")
        col = graphs_collection()
        
        query = {"user_id": user_id}
        if graph_type:
            query["graph_type"] = graph_type
        
        cursor = col.find(query).sort("updated_at", -1).skip(skip).limit(limit)
        graphs = await cursor.to_list(length=limit)
        
        logger.info(f"Found {len(graphs)} graphs for user {user_id}")
        return graphs
        
    except Exception as e:
        logger.error(f"Error getting user graphs: {str(e)}")
        raise


async def update_graph(graph_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """
    Update a graph. Only updates provided fields.
    
    Args:
        graph_id: The graph ID
        user_id: The user ID (for authorization)
        update_data: Dictionary of fields to update
        
    Returns:
        Updated graph document or None if not found
        
    Raises:
        ValueError: If trying to update to a name that already exists
    """
    try:
        logger.info(f"Updating graph {graph_id} for user {user_id}")
        col = graphs_collection()
        
        # If updating graph_name, check for duplicates
        if "graph_name" in update_data:
            # Get current graph to know its type
            current_graph = await col.find_one({
                "_id": ObjectId(graph_id),
                "user_id": user_id
            })
            
            if not current_graph:
                logger.warning(f"Graph {graph_id} not found for user {user_id}")
                return None
            
            # Check if new name conflicts with existing graphs of same type
            existing = await col.find_one({
                "user_id": user_id,
                "graph_name": update_data["graph_name"],
                "graph_type": current_graph["graph_type"],
                "_id": {"$ne": ObjectId(graph_id)}
            })
            
            if existing:
                logger.warning(f"Graph name '{update_data['graph_name']}' already exists for user {user_id}")
                raise ValueError(f"A {current_graph['graph_type']} graph named '{update_data['graph_name']}' already exists. Please use a different name.")
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update document
        result = await col.find_one_and_update(
            {"_id": ObjectId(graph_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Graph {graph_id} updated successfully")
        else:
            logger.warning(f"Graph {graph_id} not found for user {user_id}")
            
        return result
        
    except ValueError as ve:
        # Re-raise validation errors
        raise ve
    except Exception as e:
        logger.error(f"Error updating graph: {str(e)}")
        raise


async def delete_graph(graph_id: str, user_id: str) -> bool:
    """
    Delete a graph.
    
    Args:
        graph_id: The graph ID
        user_id: The user ID (for authorization)
        
    Returns:
        True if deleted, False if not found
    """
    try:
        logger.info(f"Deleting graph {graph_id} for user {user_id}")
        col = graphs_collection()
        
        result = await col.delete_one({
            "_id": ObjectId(graph_id),
            "user_id": user_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"Graph {graph_id} deleted successfully")
            return True
        else:
            logger.warning(f"Graph {graph_id} not found for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting graph: {str(e)}")
        raise


async def count_user_graphs(user_id: str, graph_type: Optional[str] = None) -> int:
    """
    Count total graphs for a user.
    
    Args:
        user_id: The user ID
        graph_type: Optional filter by graph type
        
    Returns:
        Total count of graphs
    """
    try:
        col = graphs_collection()
        
        query = {"user_id": user_id}
        if graph_type:
            query["graph_type"] = graph_type
        
        count = await col.count_documents(query)
        return count
        
    except Exception as e:
        logger.error(f"Error counting user graphs: {str(e)}")
        raise
