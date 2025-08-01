from fastapi import APIRouter, WebSocket
from typing import List
from app.services.wikipedia_service import fetch_relationships,getPersonalDetails
from app.models.genealogy import Relationship,personalInfo

router = APIRouter()

@router.get("/relationships/{page_title}/{depth}", response_model=List[Relationship])
async def get_relationships(page_title: str, depth: int):
    print(page_title,depth)
    relationships = await fetch_relationships(page_title, depth)
    return relationships

@router.get('/info/{page_title}',response_model=personalInfo)
async def get_personal_details(page_title:str):
    personal_info= await getPersonalDetails(page_title=page_title)
    return personal_info
    

@router.websocket("/ws/relationships")
async def websocket_relationships(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        page_title, depth = data.split(",")
        print(f"Received request for {page_title} with depth {depth}")
        relationships = await fetch_relationships(page_title, int(depth))
        await websocket.send_json(relationships)