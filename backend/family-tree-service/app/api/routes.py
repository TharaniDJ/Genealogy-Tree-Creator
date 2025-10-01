# from fastapi import APIRouter, WebSocket
# from typing import List
# from app.services.wikipedia_service import fetch_relationships,getPersonalDetails
# from app.models.genealogy import Relationship,personalInfo

# router = APIRouter()

# @router.get("/relationships/{page_title}/{depth}", response_model=List[Relationship])
# async def get_relationships(page_title: str, depth: int):
#     print(page_title,depth)
#     relationships = await fetch_relationships(page_title, depth)
#     return relationships

# @router.get('/info/{page_title}',response_model=personalInfo)
# async def get_personal_details(page_title:str):
#     personal_info= await getPersonalDetails(page_title=page_title)
#     return personal_info
    

# @router.websocket("/ws/relationships")
# async def websocket_relationships(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         page_title, depth = data.split(",")
#         print(f"Received request for {page_title} with depth {depth}")
#         relationships = await fetch_relationships(page_title, int(depth))
#         await websocket.send_json(relationships)

""" from fastapi import APIRouter, WebSocket
from typing import List
from app.services.wikipedia_service import fetch_relationships,getPersonalDetails
from app.models.genealogy import Relationship,personalInfo
from app.services.template_tree_extractor import extract_relationships_from_page
router = APIRouter()

@router.get("/family-tree/{title}")
async def get_family_tree(title: str):
    relationships = extract_relationships_from_page(title)
    return {"title": title, "relationships": relationships}


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

@router.websocket("/ws/family-tree")
async def websocket_family_tree(websocket: WebSocket):
    await websocket.accept()
    while True:
        title = await websocket.receive_text()
        relationships = extract_relationships_from_page(title)
        await websocket.send_json({
            "title": title,
            "relationships": relationships
        })


 """
""" from fastapi import APIRouter, WebSocket
from typing import List
from app.services.wikipedia_service import fetch_relationships, getPersonalDetails
from app.models.genealogy import Relationship, personalInfo
from app.services.template_tree_extractor import extract_relationships_from_page, extract_relationships_from_page_streaming
from app.core.websocket_manager import WebSocketManager

router = APIRouter()

@router.get("/family-tree/{title}")
async def get_family_tree(title: str):
    relationships = extract_relationships_from_page(title)
    return {"title": title, "relationships": relationships}

@router.get("/relationships/{page_title}/{depth}", response_model=List[Relationship])
async def get_relationships(page_title: str, depth: int):
    print(page_title, depth)
    relationships = await fetch_relationships(page_title, depth)
    return relationships

@router.get('/info/{page_title}', response_model=personalInfo)
async def get_personal_details(page_title: str):
    personal_info = await getPersonalDetails(page_title=page_title)
    return personal_info

@router.websocket("/ws/relationships")
async def websocket_relationships(websocket: WebSocket):
    await websocket.accept()
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [websocket]  # Add this websocket to manager
    
    while True:
        try:
            data = await websocket.receive_text()
            page_title, depth = data.split(",")
            print(f"Received request for {page_title} with depth {depth}")
            
            # Use the streaming version that sends one relationship at a time
            relationships = await fetch_relationships(page_title, int(depth), websocket_manager)
            
        except Exception as e:
            print(f"Error in websocket_relationships: {e}")
            break

@router.websocket("/ws/family-tree")
async def websocket_family_tree(websocket: WebSocket):
    await websocket.accept()
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [websocket]  # Add this websocket to manager
    
    while True:
        try:
            title = await websocket.receive_text()
            print(f"Received family tree request for: {title}")
            
            # Use the NEW streaming function instead of the old one
            relationships = await extract_relationships_from_page_streaming(title, websocket_manager)
            
            # Send final completion message
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "title": title,
                    "total_relationships": len(relationships)
                }
            })
            
        except Exception as e:
            print(f"Error in websocket_family_tree: {e}")
            await websocket.send_json({
                "type": "error", 
                "data": {"message": str(e)}
            })
            break """

from fastapi import APIRouter, WebSocket
from typing import List
from app.services.wikipedia_service import fetch_relationships, fetch_relationships_by_qid, getPersonalDetails
from app.models.genealogy import Relationship, personalInfo
from app.services.template_tree_extractor import extract_relationships_from_page, extract_relationships_from_page_streaming
from app.core.websocket_manager import WebSocketManager

router = APIRouter()

@router.get("/family-tree/{title}")
async def get_family_tree(title: str):
    relationships = extract_relationships_from_page(title)
    return {"title": title, "relationships": relationships}

@router.get("/relationships/{page_title}/{depth}", response_model=List[Relationship])
async def get_relationships(page_title: str, depth: int):
    print(page_title, depth)
    relationships = await fetch_relationships(page_title, depth)
    return relationships

@router.get('/info/{page_title}', response_model=personalInfo)
async def get_personal_details(page_title: str):
    personal_info = await getPersonalDetails(page_title=page_title)
    return personal_info

# NEW: QID-based expansion endpoint
@router.post("/expand-by-qid")
async def expand_genealogy_by_qid(request: dict):
    """
    Expand genealogy tree using existing QID (no name lookup needed).
    Request format: {"qid": "Q12345", "depth": 3, "entity_name": "Optional Name"}
    """
    try:
        qid = request.get("qid")
        depth = request.get("depth", 3)
        entity_name = request.get("entity_name")
        
        if not qid:
            return {"error": "QID is required"}
        
        print(f"QID-based expansion request: QID={qid}, depth={depth}, entity={entity_name}")
        
        # For now, return synchronously - you can add WebSocket support later if needed
        relationships = await fetch_relationships_by_qid(
            qid=qid,
            depth=depth,
            websocket_manager=None,  # No WebSocket for this endpoint
            entity_name=entity_name
        )
        
        return {
            "success": True,
            "qid": qid,
            "entity_name": entity_name,
            "relationships_count": len(relationships),
            "relationships": relationships
        }
        
    except Exception as e:
        print(f"Error in expand_genealogy_by_qid: {e}")
        return {"error": str(e)}

@router.websocket("/ws/relationships")
async def websocket_relationships(websocket: WebSocket):
    await websocket.accept()
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [websocket]  # Add this websocket to manager
    
    while True:
        try:
            data = await websocket.receive_text()
            page_title, depth = data.split(",")
            print(f"Received request for {page_title} with depth {depth}")
            
            # Use the streaming version that sends one relationship at a time
            relationships = await fetch_relationships(page_title, int(depth), websocket_manager)
            
        except Exception as e:
            print(f"Error in websocket_relationships: {e}")
            break

# NEW: WebSocket endpoint for QID-based expansion with real-time updates
@router.websocket("/ws/expand-by-qid")
async def websocket_expand_by_qid(websocket: WebSocket):
    await websocket.accept()
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [websocket]
    
    while True:
        try:
            data = await websocket.receive_text()
            # Expected format: "Q12345,3,Entity Name" or "Q12345,3"
            parts = data.split(",")
            qid = parts[0].strip()
            depth = int(parts[1].strip())
            entity_name = parts[2].strip() if len(parts) > 2 else None
            
            print(f"WebSocket QID expansion: QID={qid}, depth={depth}, entity={entity_name}")
            
            # Validate QID format
            if not qid.startswith('Q') or not qid[1:].isdigit():
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Invalid QID format: {qid}"}
                })
                continue
            
            # Use QID-based fetch with WebSocket streaming
            relationships = await fetch_relationships_by_qid(
                qid=qid,
                depth=depth,
                websocket_manager=websocket_manager,
                entity_name=entity_name
            )
            
            # Send completion message
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "qid": qid,
                    "entity_name": entity_name,
                    "total_relationships": len(relationships)
                }
            })
            
        except ValueError as e:
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Invalid data format. Expected: 'Q12345,3,Entity Name'. Error: {e}"}
            })
        except Exception as e:
            print(f"Error in websocket_expand_by_qid: {e}")
            await websocket.send_json({
                "type": "error", 
                "data": {"message": str(e)}
            })
            break

@router.websocket("/ws/family-tree")
async def websocket_family_tree(websocket: WebSocket):
    await websocket.accept()
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [websocket]  # Add this websocket to manager
    
    while True:
        try:
            title = await websocket.receive_text()
            print(f"Received family tree request for: {title}")
            
            # Use the NEW streaming function instead of the old one
            relationships = await extract_relationships_from_page_streaming(title, websocket_manager)
            
            # Send final completion message
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "title": title,
                    "total_relationships": len(relationships)
                }
            })
            
        except Exception as e:
            print(f"Error in websocket_family_tree: {e}")
            await websocket.send_json({
                "type": "error", 
                "data": {"message": str(e)}
            })
            break