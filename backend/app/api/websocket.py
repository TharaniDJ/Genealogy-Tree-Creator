from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
from app.core.websocket_manager import WebSocketManager
from app.services.wikipedia_service import fetch_relationships

router = APIRouter()
manager = WebSocketManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the incoming message
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "fetch_relationships":
                    page_title = message.get("page_title")
                    depth = message.get("depth", 2)
                    
                    if page_title:
                        # Start fetching relationships and send them one by one
                        await manager.send_status("Starting to fetch relationships...", 0)
                        relationships = await fetch_relationships(page_title, depth, manager)
                        await manager.send_status("All relationships fetched!", 100)
                    else:
                        await manager.send_message(json.dumps({
                            "type": "error",
                            "data": {"message": "page_title is required"}
                        }))
                else:
                    await manager.send_message(json.dumps({
                        "type": "error", 
                        "data": {"message": f"Unknown action: {action}"}
                    }))
                    
            except json.JSONDecodeError:
                await manager.send_message(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_status("A client has disconnected.")