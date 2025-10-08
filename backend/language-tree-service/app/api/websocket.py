from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
import asyncio
import app.services.wikipedia_service as wiki
from app.core.shared import websocket_manager

router = APIRouter()

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
            raw = data
            data = data.strip("\"")
            print(f"Received WebSocket request: {data}")
            
            try:
                # Try to parse JSON-based actions first
                parsed = None
                if raw.strip().startswith("{"):
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = None

                if isinstance(parsed, dict) and parsed.get("action"):
                    action = parsed.get("action")
                    if action == "expand_by_qid":
                        await websocket_manager.send_error(
                            "Expansion by QID is no longer supported.",
                            connection_id
                        )
                        continue
                        
                    elif action == "expand_by_label":
                        # Fallback: expand using a label by reusing depth-1 fetch
                        label_value = parsed.get("label")
                        if not isinstance(label_value, str) or not label_value.strip():
                            raise ValueError("Missing or invalid 'label' for expand_by_label")
                        label = label_value.strip()
                        await websocket_manager.send_status(
                            f"Expanding node '{label}' (depth 1)...",
                            0,
                            connection_id
                        )
                        
                        # Create a task for the expansion operation
                        async def expand_by_label_task(label_name: str):
                            try:
                                relationships = await wiki.fetch_language_relationships(
                                    label_name,
                                    1,
                                    websocket_manager,
                                    connection_id
                                )
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_json({
                                        "type": "expand_complete",
                                        "data": {"label": label_name, "added": len(relationships)}
                                    }, connection_id)
                            except asyncio.CancelledError:
                                print(f"Expand by label task cancelled for connection {connection_id}")
                                raise
                            except Exception as e:
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_error(f"Error expanding node: {str(e)}", connection_id)
                        
                        # Start the task and register it
                        task = asyncio.create_task(expand_by_label_task(label))
                        websocket_manager.set_active_task(connection_id, task)
                        await task
                        continue

                # Legacy format: "language_name,depth"
                # Parse the request
                if "," in data:
                    language_name, depth_str = data.split(",", 1)
                    depth = int(depth_str.strip())
                else:
                    raise ValueError("Invalid format. Expected 'language_name,depth' or a JSON action")
                
                if depth < 1 or depth > 5:
                    raise ValueError("Depth must be between 1 and 5")
                
                print(f"Processing request for {language_name} with depth {depth}")
                
                # Send initial status
                await websocket_manager.send_status(
                    f"Starting language tree exploration for {language_name}...", 
                    0, 
                    connection_id
                )
                
                # Create a task for the main exploration
                async def exploration_task():
                    try:
                        # Fetch relationships with real-time updates
                        relationships = await wiki.fetch_language_relationships(
                            language_name, 
                            depth, 
                            websocket_manager,
                            connection_id
                        )
                        
                        # Send final result if connection is still active
                        if websocket_manager.is_connection_active(connection_id):
                            await websocket_manager.send_json({
                                "type": "complete",
                                "data": {
                                    "language": language_name,
                                    "depth": depth,
                                    "total_relationships": len(relationships),
                                    "relationships": relationships
                                }
                            }, connection_id)
                    except asyncio.CancelledError:
                        print(f"Exploration task cancelled for connection {connection_id}")
                        raise
                    except Exception as e:
                        if websocket_manager.is_connection_active(connection_id):
                            await websocket_manager.send_error(f"Error processing request: {str(e)}", connection_id)
                
                # Start the task and register it
                task = asyncio.create_task(exploration_task())
                websocket_manager.set_active_task(connection_id, task)
                await task
                
            except ValueError as e:
                await websocket_manager.send_error(f"Invalid request: {str(e)}", connection_id)
            except asyncio.CancelledError:
                print(f"WebSocket task cancelled for connection {connection_id}")
                break
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
