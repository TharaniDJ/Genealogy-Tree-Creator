from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.wikipedia_service import fetch_language_relationships, get_distribution_map_image,fetch_language_info
from app.models.language import LanguageRelationship, LanguageInfo, DistributionMapResponse
from app.models.graph import GraphSaveRequest, GraphResponse, GraphUpdateRequest
from app.services.graph_repository import graph_repo

from app.services.generate_relationships import start_dataset_generation, get_task_status
router = APIRouter()

@router.get("/relationships/{language_name}/{depth}", response_model=List[LanguageRelationship])
async def get_language_relationships(language_name: str, depth: int):
    """
    Get language family relationships for a given language and depth.
    
    - **language_name**: Name of the language (e.g., "English", "Spanish")
    - **depth**: How many levels deep to explore (1-5)
    """
    if depth < 1 or depth > 5:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 5")
    
    print(f"Fetching relationships for {language_name} with depth {depth}")
    try:
        relationships = await fetch_language_relationships(language_name, depth)
        return relationships
    except Exception as e:
        print(f"Error fetching relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")

@router.get("/distribution-map/{qid}", response_model=DistributionMapResponse)
async def get_distribution_map(qid: str):
    """
    Get distribution map image URL for a given language QID.
    
    - **qid**: Wikidata QID (e.g., "Q1860" for English)
    """
    print(f"Fetching distribution map for QID: {qid}")
    try:
        # Validate QID format (should start with Q and be followed by digits)
        if not qid.startswith('Q') or not qid[1:].isdigit():
            raise HTTPException(status_code=400, detail="Invalid QID format. QID should start with 'Q' followed by digits.")
        
        image_url = get_distribution_map_image(qid)
        return DistributionMapResponse(
            qid=qid,
            image_url=image_url,
            found=image_url is not None
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching distribution map: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching distribution map: {str(e)}")
@router.post('/create-dataset')
async def create_dataset():
    """
    Start dataset generation as a background task.
    Returns immediately with a task ID to track progress.
    """
    try:
        task_id = start_dataset_generation()
        return {
            "message": "Dataset generation started",
            "task_id": task_id,
            "status_endpoint": f"/dataset-status/{task_id}"
        }
    except Exception as e:
        print(f'Error starting dataset creation: {e}')
        raise HTTPException(status_code=500, detail=f"Error starting dataset creation: {str(e)}")

@router.get('/dataset-status/{task_id}')
async def get_dataset_status(task_id: str):
    """
    Get the status of a dataset generation task.
    """
    try:
        status = get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        print(f'Error getting dataset status: {e}')
        raise HTTPException(status_code=500, detail=f"Error getting dataset status: {str(e)}")
@router.get('/info/{qid}', response_model=LanguageInfo)
async def get_language_info(qid: str):
    """
    Get detailed information about a specific language.
    
    - **qid**: Wikidata QID of the language (e.g., "Q1860" for English)
    """
    try:
        language_info = await fetch_language_info(qid)
        if not language_info:
            raise HTTPException(status_code=404, detail=f"Language '{qid}' not found")
        return language_info
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching language info: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching language info: {str(e)}")
# @router.get('/info/{language_name}', response_model=LanguageInfo)
# async def get_language_info(language_name: str):
#     """
#     Get detailed information about a specific language.
    
#     - **language_name**: Name of the language (e.g., "English", "Spanish")
#     """
#     print(f"Fetching info for {language_name}")
#     try:
#         language_info = await get_language_details(language_name)
#         if not language_info:
#             raise HTTPException(status_code=404, detail=f"Language '{language_name}' not found")
#         return language_info
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error fetching language info: {e}")
#         raise HTTPException(status_code=500, detail=f"Error fetching language info: {str(e)}")

@router.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "language-tree-service"}

@router.get('/stats')
async def get_service_stats():
    """Get service statistics"""
    return {
        "service": "language-tree-service",
        "version": "1.0.0",
        "endpoints": [
            "/relationships/{language_name}/{depth}",
            "/distribution-map/{qid}",
            "/info/{qid}",
            "/create-dataset",
            "/dataset-status/{task_id}",
            "/health",
            "/stats"
        ]
    }

# ------------------ Graph Save/Retrieve APIs ------------------

@router.post('/graphs', response_model=GraphResponse)
async def save_graph(graph: GraphSaveRequest):
    """
    Save a graph for a user. Uses placeholder MongoDB repository.
    - user_id: defaults to "1234" if not provided
    - name: graph name (defaults to search name from client)
    - depth, node_count, relationships: describe the graph
    """
    try:
        if not graph.name:
            raise HTTPException(status_code=400, detail="Graph name is required")
        resp = await graph_repo.save_graph(graph)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving graph: {str(e)}")


@router.get('/graphs/{user_id}', response_model=List[GraphResponse])
async def get_graphs_for_user(user_id: str):
    """Return all graphs for a user."""
    try:
        return await graph_repo.get_graphs_for_user(user_id)
    except Exception as e:
        print(f"Error retrieving graphs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving graphs: {str(e)}")


@router.get('/graphs/{user_id}/by-name/{name}', response_model=GraphResponse)
async def get_graph_by_name(user_id: str, name: str):
    """Return a specific graph for a user by name."""
    try:
        g = await graph_repo.get_graph_by_name(user_id, name)
        if not g:
            raise HTTPException(status_code=404, detail="Graph not found")
        return g
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving graph by name: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving graph: {str(e)}")


@router.put('/graphs/{user_id}/by-name/{name}', response_model=GraphResponse)
async def update_graph(user_id: str, name: str, update: GraphUpdateRequest):
    """Update a user's graph by name. Supports renaming and content updates."""
    try:
        g = await graph_repo.update_graph(user_id, name, update)
        if not g:
            raise HTTPException(status_code=404, detail="Graph not found")
        return g
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating graph: {str(e)}")


@router.delete('/graphs/{user_id}/by-name/{name}')
async def delete_graph(user_id: str, name: str):
    """Delete a user's graph by name."""
    try:
        ok = await graph_repo.delete_graph(user_id, name)
        if not ok:
            raise HTTPException(status_code=404, detail="Graph not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting graph: {str(e)}")
