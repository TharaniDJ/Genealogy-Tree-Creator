"""from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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
        await manager.send_status("A client has disconnected.")"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

from app.core.websocket_manager import WebSocketManager
from app.services.wikipedia_service import (
    fetch_relationships,
    fetch_relationships_from_tree
)

router = APIRouter()
manager = WebSocketManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "fetch_relationships":
                    page_title = message.get("page_title")
                    depth = message.get("depth", 2)

                    if page_title:
                        await manager.send_status("Starting to fetch relationships...", 0)

                        # Step 1: Try wikitext-based tree extraction
                        tree_relationships = fetch_relationships_from_tree(page_title)
                        await manager.send_status("Parsed family tree template (if available).", 30)

                        # Step 2: SPARQL extraction from Wikidata
                        sparql_relationships = await fetch_relationships(page_title, depth, manager)
                        await manager.send_status("Fetched Wikidata relationships.", 80)

                        # Step 3: Combine both
                        combined_relationships = tree_relationships + sparql_relationships

                        # Step 4: Send result
                        await manager.send_message(json.dumps({
                            "type": "relationships",
                            "data": combined_relationships
                        }))
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
