from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
from app.core.websocket_manager import WebSocketManager
from app.services.wikipedia_service import fetch_relationships
import asyncio

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

@router.websocket("/ws-test")
async def websocket_test_endpoint(websocket: WebSocket):
    numebr_of_nodes = 30
    await manager.connect(websocket)
    try:
        # First, wait for client to send the initial request
        data = await websocket.receive_text()
        
        # Parse the incoming message
        try:
            message = json.loads(data)
            action = message.get("action")
            
            if action == "fetch_relationships":
                # Test messages to send one by one
                test_messages = [
                    {"type": "status", "data": {"message": "Starting to fetch relationships...", "progress": 0}},
                    {"type": "status", "data": {"message": "Starting relationship collection...", "progress": 0}},

                    {"type": "personal_details", "data": {"entity": "Albert Einstein", "qid": "Q937", "birth_year": "1879", "death_year": "1955", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Albert%20Einstein%20Head.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "child of", "entity2": "Hermann Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Hermann Einstein", "qid": "Q88665", "birth_year": "1847", "death_year": "1902", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Hermann%20einstein.jpg"}},

                    {"type": "relationship", "data": {"entity1": "Hermann Einstein", "relationship": "child of", "entity2": "Abraham Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Abraham Einstein", "qid": "Q30277523", "birth_year": "1808", "death_year": "1868", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Abraham%20Einstein.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Hermann Einstein", "relationship": "child of", "entity2": "Helen Einstein"}},

                    {"type": "personal_details", "data": {"entity": "Helen Einstein", "qid": "Q30278245", "birth_year": "1814", "death_year": "1887", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Helen%20Einstein.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Hermann Einstein", "relationship": "spouse of", "entity2": "Pauline Koch"}},
                    {"type": "personal_details", "data": {"entity": "Pauline Koch", "qid": "Q4357787", "birth_year": "1858", "death_year": "1920", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Pauline%20Koch.jpg"}},

                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "child of", "entity2": "Pauline Koch"}},
                    {"type": "relationship", "data": {"entity1": "Pauline Koch", "relationship": "child of", "entity2": "Julius Koch"}},
                    {"type": "personal_details", "data": {"entity": "Julius Koch", "qid": "Q1712755", "birth_year": "1816", "death_year": "1895", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Julius%20Koch%20Cannstatt.jpg"}},

                    {"type": "relationship", "data": {"entity1": "Pauline Koch", "relationship": "child of", "entity2": "Annette Bernheimer"}},
                    {"type": "personal_details", "data": {"entity": "Annette Bernheimer", "qid": "Q30283429", "birth_year": "1825", "death_year": "1886", "image_url": None}},
                    {"type": "relationship", "data": {"entity1": "Pauline Koch", "relationship": "spouse of", "entity2": "Hermann Einstein"}},
                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "spouse of", "entity2": "Mileva Marić"}},
                    {"type": "personal_details", "data": {"entity": "Mileva Marić", "qid": "Q76346", "birth_year": "1875", "death_year": "1948", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Mileva%20Maric%201912.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "spouse of", "entity2": "Elsa Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Elsa Einstein", "qid": "Q68761", "birth_year": "1876", "death_year": "1936", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Bundesarchiv%20Bild%20102-00486A%2C%20Elsa%20Einstein.jpg"}},
                    {"type": "status", "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}},
                    {"type": "relationship", "data": {"entity1": "Hans Albert Einstein", "relationship": "child of", "entity2": "Albert Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Hans Albert Einstein", "qid": "Q123371", "birth_year": "1904", "death_year": "1973", "image_url": None}},
                    {"type": "relationship", "data": {"entity1": "Hans Albert Einstein", "relationship": "child of", "entity2": "Mileva Marić"}},
                    {"type": "relationship", "data": {"entity1": "Bernhard Caesar Einstein", "relationship": "child of", "entity2": "Hans Albert Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Bernhard Caesar Einstein", "qid": "Q824855", "birth_year": "1930", "death_year": "2008", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Bernard%20Einstein.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Evelyn Einstein", "relationship": "child of", "entity2": "Hans Albert Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Evelyn Einstein", "qid": "Q432375", "birth_year": "1941", "death_year": "2011", "image_url": None}},
                    {"type": "relationship", "data": {"entity1": "Hans Albert Einstein", "relationship": "spouse of", "entity2": "Elizabeth Roboz Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Elizabeth Roboz Einstein", "qid": "Q57515793", "birth_year": "1904", "death_year": "1995", "image_url": "http://commons.wikimedia.org/wiki/Special:FilePath/Elizabeth%20Roboz%20Einstein%20%281904-1995%29%20%288491285511%29.jpg"}},
                    {"type": "relationship", "data": {"entity1": "Eduard Einstein", "relationship": "child of", "entity2": "Albert Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Eduard Einstein", "qid": "Q118253", "birth_year": "1910", "death_year": "1965", "image_url": None}},
                    {"type": "relationship", "data": {"entity1": "Eduard Einstein", "relationship": "child of", "entity2": "Mileva Marić"}},
                    {"type": "relationship", "data": {"entity1": "Lieserl (Einstein)", "relationship": "child of", "entity2": "Albert Einstein"}},
                    {"type": "personal_details", "data": {"entity": "Lieserl (Einstein)", "qid": "Q468357", "birth_year": "1902", "death_year": "1903", "image_url": None}},
                    {"type": "relationship", "data": {"entity1": "Lieserl (Einstein)", "relationship": "child of", "entity2": "Mileva Marić"}},
                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "spouse of", "entity2": "Mileva Marić"}},
                    {"type": "relationship", "data": {"entity1": "Albert Einstein", "relationship": "spouse of", "entity2": "Elsa Einstein"}},
                    {"type": "status", "data": {"message": "Collection complete!", "progress": 100}},
                    {"type": "status", "data": {"message": "All relationships fetched!", "progress": 100}}
                ]
                
                # Send each message with a delay
                for message in test_messages[0:2+numebr_of_nodes]+test_messages[-2:]:
                    await manager.send_message(json.dumps(message))
                    await asyncio.sleep(1)  # 1 second delay between messages
                    
        except json.JSONDecodeError:
            await manager.send_message(json.dumps({
                "type": "error",
                "data": {"message": "Invalid JSON format"}
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
