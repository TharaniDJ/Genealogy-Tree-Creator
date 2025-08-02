from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
from app.services.wikipedia_service import fetch_species_relationships, get_taxonomic_classification
from app.core.websocket_manager import WebSocketManager

router = APIRouter()

# Create a global WebSocket manager instance
websocket_manager = WebSocketManager()

@router.websocket("/ws/relationships")
async def websocket_species_relationships(websocket: WebSocket):
    """
    WebSocket endpoint for real-time species relationship exploration.
    
    Send: "species_name,depth" (e.g., "Panthera leo,2")
    Receive: Real-time updates with relationships and species details
    """
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, connection_id)
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            print(f"Received WebSocket request: {data}")
            
            try:
                # Parse the request
                if "," in data:
                    species_name, depth_str = data.split(",", 1)
                    depth = int(depth_str.strip())
                else:
                    raise ValueError("Invalid format. Expected 'species_name,depth'")
                
                if depth < 1 or depth > 6:
                    raise ValueError("Depth must be between 1 and 6")
                
                print(f"Processing request for {species_name} with depth {depth}")
                
                # Send initial status
                await websocket_manager.send_status(
                    f"Starting taxonomic tree exploration for {species_name}...", 
                    0, 
                    connection_id
                )
                
                # Fetch relationships with real-time updates
                relationships = await fetch_species_relationships(
                    species_name, 
                    depth, 
                    websocket_manager
                )
                
                # Send final result
                await websocket_manager.send_json({
                    "type": "complete",
                    "data": {
                        "species": species_name,
                        "depth": depth,
                        "total_relationships": len(relationships),
                        "relationships": relationships
                    }
                }, connection_id)
                
            except ValueError as e:
                await websocket_manager.send_error(f"Invalid request: {str(e)}", connection_id)
            except Exception as e:
                print(f"Error processing WebSocket request: {e}")
                await websocket_manager.send_error(f"Error processing request: {str(e)}", connection_id)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {connection_id}")
    finally:
        websocket_manager.disconnect(connection_id)

@router.websocket("/ws/taxonomy")
async def websocket_taxonomy(websocket: WebSocket):
    """
    WebSocket endpoint for real-time taxonomic classification exploration.
    
    Send: "species_name" (e.g., "Panthera leo")
    Receive: Complete taxonomic classification
    """
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, connection_id)
    
    try:
        while True:
            # Receive data from client
            species_name = await websocket.receive_text()
            print(f"Received taxonomy request: {species_name}")
            
            try:
                # Send initial status
                await websocket_manager.send_status(
                    f"Getting taxonomic classification for {species_name}...", 
                    0, 
                    connection_id
                )
                
                # Get QID and classification
                from app.services.wikipedia_service import get_species_qid
                qid = get_species_qid(species_name)
                
                if not qid:
                    await websocket_manager.send_error(f"Species '{species_name}' not found", connection_id)
                    continue
                
                # Get taxonomic classification
                classification = await get_taxonomic_classification(qid)
                
                # Send result
                await websocket_manager.send_json({
                    "type": "taxonomy_complete",
                    "data": {
                        "species": species_name,
                        "qid": qid,
                        "classification": classification
                    }
                }, connection_id)
                
            except Exception as e:
                print(f"Error processing taxonomy request: {e}")
                await websocket_manager.send_error(f"Error processing request: {str(e)}", connection_id)
                
    except WebSocketDisconnect:
        print(f"Taxonomy WebSocket disconnected: {connection_id}")
    finally:
        websocket_manager.disconnect(connection_id)

@router.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for service status updates"""
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, connection_id)
    
    try:
        # Send initial status
        await websocket_manager.send_json({
            "type": "status",
            "data": {
                "service": "species-tree-service",
                "status": "connected",
                "connection_id": connection_id,
                "active_connections": websocket_manager.get_connection_count()
            }
        }, connection_id)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()  # Wait for ping/keepalive
            
    except WebSocketDisconnect:
        print(f"Status WebSocket disconnected: {connection_id}")
    finally:
        websocket_manager.disconnect(connection_id)
