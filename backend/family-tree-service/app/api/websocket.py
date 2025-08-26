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
            print(f"Received data: {data}")  # Print received data
            
            # Parse the incoming message
            try:
                message = json.loads(data)
                print(f"Parsed message: {message}")  # Print parsed message
                action = message.get("action")
                print(f"Action: {action}")  # Print action
                
                if action == "fetch_relationships":
                    page_title = message.get("page_title")
                    depth = message.get("depth", 2)
                    print(f"Fetching relationships for: {page_title}, depth: {depth}")  # Print fetch info
                    
                    if page_title:
                        # Start fetching relationships and send them one by one
                        await manager.send_status("Starting to fetch relationships...", 0)
                        try:
                            relationships = await fetch_relationships(page_title, depth, manager)
                        except Exception as error:
                            print(f"Error fetching relationships: {error}")  # Print error
                            await manager.send_message(json.dumps({
                                "type": "error",
                                "data": {"message": f"Error fetching relationships: {error}"}
                            }))
                            return
                        print(f"Fetched relationships: {relationships}")  # Print fetched relationships
                        await manager.send_status("All relationships fetched!", 100)
                    else:
                        print("Error: page_title is required")  # Print error
                        await manager.send_message(json.dumps({
                            "type": "error",
                            "data": {"message": "page_title is required"}
                        }))
                else:
                    print(f"Error: Unknown action: {action}")  # Print error
                    await manager.send_message(json.dumps({
                        "type": "error", 
                        "data": {"message": f"Unknown action: {action}"}
                    }))
                    
            except json.JSONDecodeError:
                print("Error: Invalid JSON format")  # Print error
                await manager.send_message(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_status("A client has disconnected.")