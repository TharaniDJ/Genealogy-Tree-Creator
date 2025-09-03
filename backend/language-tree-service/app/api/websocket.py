from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
from app.services.wikipedia_service import fetch_language_relationships
from app.core.websocket_manager import WebSocketManager

router = APIRouter()

# Create a global WebSocket manager instance
websocket_manager = WebSocketManager()

@router.websocket("/ws/relationships")
async def websocket_language_relationships(websocket: WebSocket):
    """
    WebSocket endpoint for real-time language relationship exploration.
    
    Send: "language_name,depth" (e.g., "English,2")
    Receive: Real-time updates with relationships and language details
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
                    language_name, depth_str = data.split(",", 1)
                    depth = int(depth_str.strip())
                else:
                    raise ValueError("Invalid format. Expected 'language_name,depth'")
                
                
                
                print(f"Processing request for {language_name} with depth {depth}")
                
                # Send initial status
                await websocket_manager.send_status(
                    f"Starting language tree exploration for {language_name}...", 
                    0, 
                    connection_id
                )
                
                # Fetch relationships with real-time updates
                relationships = await fetch_language_relationships(
                    language_name, 
                    depth, 
                    websocket_manager
                )
                
                # Send final result
                await websocket_manager.send_json({
                    "type": "complete",
                    "data": {
                        "language": language_name,
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
                "service": "language-tree-service",
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
