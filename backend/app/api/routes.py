from fastapi import APIRouter, WebSocket
from typing import List
from app.services.wikipedia_service import fetch_relationships
from app.models.genealogy import Relationship

router = APIRouter()

@router.get("/relationships/{page_title}/{depth}", response_model=List[Relationship])
async def get_relationships(page_title: str, depth: int):
    relationships = await fetch_relationships(page_title, depth)
    return relationships

@router.websocket("/ws/relationships")
async def websocket_relationships(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        page_title, depth = data.split(",")
        relationships = await fetch_relationships(page_title, int(depth))
        await websocket.send_json(relationships)