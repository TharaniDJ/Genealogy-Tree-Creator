# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from typing import List
# import json
# from app.core.websocket_manager import WebSocketManager
# from app.services.wikipedia_service import fetch_relationships

# router = APIRouter()
# manager = WebSocketManager()

# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             print(f"Received data: {data}")  # Print received data
            
#             # Parse the incoming message
#             try:
#                 message = json.loads(data)
#                 print(f"Parsed message: {message}")  # Print parsed message
#                 action = message.get("action")
#                 print(f"Action: {action}")  # Print action
                
#                 if action == "fetch_relationships":
#                     page_title = message.get("page_title")
#                     depth = message.get("depth", 2)
#                     print(f"Fetching relationships for: {page_title}, depth: {depth}")  # Print fetch info
                    
#                     if page_title:
#                         # Start fetching relationships and send them one by one
#                         await manager.send_status("Starting to fetch relationships...", 0)
#                         try:
#                             relationships = await fetch_relationships(page_title, depth, manager)
#                         except Exception as error:
#                             print(f"Error fetching relationships: {error}")  # Print error
#                             await manager.send_message(json.dumps({
#                                 "type": "error",
#                                 "data": {"message": f"Error fetching relationships: {error}"}
#                             }))
#                             return
#                         print(f"Fetched relationships: {relationships}")  # Print fetched relationships
#                         await manager.send_status("All relationships fetched!", 100)
#                     else:
#                         print("Error: page_title is required")  # Print error
#                         await manager.send_message(json.dumps({
#                             "type": "error",
#                             "data": {"message": "page_title is required"}
#                         }))
#                 else:
#                     print(f"Error: Unknown action: {action}")  # Print error
#                     await manager.send_message(json.dumps({
#                         "type": "error", 
#                         "data": {"message": f"Unknown action: {action}"}
#                     }))
                    
#             except json.JSONDecodeError:
#                 print("Error: Invalid JSON format")  # Print error
#                 await manager.send_message(json.dumps({
#                     "type": "error",
#                     "data": {"message": "Invalid JSON format"}
#                 }))
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.send_status("A client has disconnected.")

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from app.core.websocket_manager import WebSocketManager
from app.services.wikipedia_service import fetch_relationships
from app.services.template_tree_extractor import extract_relationships_from_page

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

                # 1️⃣ Basic SPARQL relationship fetch
                if action == "fetch_relationships":
                    page_title = message.get("page_title")
                    depth = message.get("depth", 2)

                    if page_title:
                        await manager.send_status("Starting to fetch relationships...", 0)
                        relationships = await fetch_relationships(page_title, depth, manager)
                        await manager.send_status("All relationships fetched!", 100)
                    else:
                        await manager.send_message(json.dumps({
                            "type": "error",
                            "data": {"message": "page_title is required"}
                        }))

                # 2️⃣ Try existing family tree first, then SPARQL if needed
                elif action == "fetch_relationships_with_tree":
                    page_title = message.get("page_title")
                    depth = message.get("depth", 2)

                    if page_title:
                        await manager.send_status("Checking for existing family tree...", 0)

                        # Step 1: Try extracting from Wikipedia's existing ahnentafel tree
                        relationships = build_tree_from_template(page_title)
                        #relationships = extract_relationships_from_page(page_title)

                        if relationships:
                            await manager.send_message(json.dumps({
                                "type": "existing_tree",
                                "data": {
                                    "title": page_title,
                                    "relationships": relationships
                                }
                            }))
                            await manager.send_status(
                                f"Found {len(relationships)} relationships from existing tree",
                                50
                            )

                        # Step 2: If depth requirement not met, fetch more via SPARQL
                        if not relationships or len(relationships) < depth:
                            await manager.send_status("Fetching more relationships via SPARQL...", 60)
                            more_relationships = await fetch_relationships(page_title, depth, manager)

                            # Merge without duplicates
                            combined = relationships + [
                                r for r in more_relationships if r not in relationships
                            ]

                            await manager.send_message(json.dumps({
                                "type": "combined_relationships",
                                "data": {
                                    "title": page_title,
                                    "relationships": combined
                                }
                            }))
                            await manager.send_status("All relationships fetched!", 100)
                        else:
                            await manager.send_status("Depth requirement already satisfied", 100)
                    else:
                        await manager.send_message(json.dumps({
                            "type": "error",
                            "data": {"message": "page_title is required"}
                        }))

                # 3️⃣ Only fetch the existing family tree (no SPARQL)
                elif action == "fetch_existing_tree":
                    page_title = message.get("page_title")
                    if page_title:
                        await manager.send_status("Extracting existing family tree...", 0)
                        relationships = extract_relationships_from_page(page_title)
                        await manager.send_message(json.dumps({
                            "type": "existing_tree",
                            "data": {
                                "title": page_title,
                                "relationships": relationships
                            }
                        }))
                        await manager.send_status("Family tree extraction complete!", 100)
                    else:
                        await manager.send_message(json.dumps({
                            "type": "error",
                            "data": {"message": "page_title is required"}
                        }))

                # ❌ Unknown action
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
