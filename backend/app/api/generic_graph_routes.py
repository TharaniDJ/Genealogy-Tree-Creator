"""
Example backend API endpoints for the generic graph system.
This shows how the backend should structure and return graph data.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Pydantic models for type safety
class GraphNodeData(BaseModel):
    id: str
    type: str  # 'entity' or 'connection'
    label: str
    data: Dict[str, Any]
    position: Optional[Dict[str, float]] = None
    style: Optional[Dict[str, Any]] = None

class GraphEdgeData(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = None
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNodeData]
    edges: List[GraphEdgeData]

router = APIRouter()

# Example: Family tree graph
@router.get("/api/graph/family/{family_id}", response_model=GraphResponse)
async def get_family_graph(family_id: str):
    """
    Return family tree as generic graph data.
    The frontend will automatically render this as a family tree.
    """
    
    # This would typically come from a database
    if family_id == "einstein-family":
        nodes = [
            GraphNodeData(
                id="albert-einstein",
                type="entity",
                label="Albert Einstein",
                data={
                    "entityType": "person",
                    "name": "Albert Einstein",
                    "birthYear": 1879,
                    "deathYear": 1955,
                    "image": "/images/albert-einstein.jpg",
                    "description": "Theoretical physicist",
                    "profession": "Physicist",
                    "achievements": ["Nobel Prize in Physics", "Theory of Relativity"],
                    "generation": 0
                }
            ),
            GraphNodeData(
                id="mileva-maric",
                type="entity",
                label="Mileva Marić",
                data={
                    "entityType": "person",
                    "name": "Mileva Marić",
                    "birthYear": 1875,
                    "deathYear": 1948,
                    "image": "/images/mileva-maric.jpg",
                    "description": "Mathematician and physicist",
                    "profession": "Mathematician",
                    "generation": 0
                }
            ),
            GraphNodeData(
                id="marriage-einstein-maric",
                type="connection",
                label="Marriage",
                data={
                    "connectionType": "marriage",
                    "date": "1903-01-06",
                    "location": "Bern, Switzerland",
                    "duration": "1903-1919",
                    "generation": 0.5
                }
            ),
            GraphNodeData(
                id="hans-albert-einstein",
                type="entity",
                label="Hans Albert Einstein",
                data={
                    "entityType": "person",
                    "name": "Hans Albert Einstein",
                    "birthYear": 1904,
                    "deathYear": 1973,
                    "description": "Hydraulic engineer",
                    "profession": "Engineer",
                    "generation": 1
                }
            ),
            GraphNodeData(
                id="eduard-einstein",
                type="entity",
                label="Eduard Einstein",
                data={
                    "entityType": "person",
                    "name": "Eduard Einstein",
                    "birthYear": 1910,
                    "deathYear": 1965,
                    "description": "Musician and scholar",
                    "profession": "Musician",
                    "generation": 1
                }
            )
        ]
        
        edges = [
            GraphEdgeData(
                id="albert-to-marriage",
                source="albert-einstein",
                target="marriage-einstein-maric",
                type="marriage",
                data={"role": "husband"}
            ),
            GraphEdgeData(
                id="mileva-to-marriage",
                source="mileva-maric",
                target="marriage-einstein-maric",
                type="marriage",
                data={"role": "wife"}
            ),
            GraphEdgeData(
                id="marriage-to-hans",
                source="marriage-einstein-maric",
                target="hans-albert-einstein",
                type="parent-child",
                label="Son"
            ),
            GraphEdgeData(
                id="marriage-to-eduard",
                source="marriage-einstein-maric",
                target="eduard-einstein",
                type="parent-child",
                label="Son"
            )
        ]
        
        return GraphResponse(nodes=nodes, edges=edges)
    
    raise HTTPException(status_code=404, detail="Family not found")

# Example: Company organizational chart
@router.get("/api/graph/company/{company_id}", response_model=GraphResponse)
async def get_company_graph(company_id: str):
    """
    Return company org chart as generic graph data.
    The frontend will automatically render this as an organizational chart.
    """
    
    if company_id == "tech-startup":
        nodes = [
            GraphNodeData(
                id="ceo-alice",
                type="entity",
                label="Alice Johnson",
                data={
                    "entityType": "person",
                    "name": "Alice Johnson",
                    "position": "Chief Executive Officer",
                    "department": "Executive",
                    "email": "alice@company.com",
                    "hireDate": "2020-01-01",
                    "image": "/images/alice-johnson.jpg",
                    "generation": 0
                }
            ),
            GraphNodeData(
                id="cto-bob",
                type="entity",
                label="Bob Smith",
                data={
                    "entityType": "person",
                    "name": "Bob Smith",
                    "position": "Chief Technology Officer",
                    "department": "Technology",
                    "email": "bob@company.com",
                    "hireDate": "2020-02-01",
                    "generation": 1
                }
            ),
            GraphNodeData(
                id="reports-to-1",
                type="connection",
                label="Reports To",
                data={
                    "connectionType": "employment",
                    "relationship": "reports-to",
                    "startDate": "2020-02-01",
                    "generation": 0.5
                }
            ),
            GraphNodeData(
                id="dev-carol",
                type="entity",
                label="Carol Davis",
                data={
                    "entityType": "person",
                    "name": "Carol Davis",
                    "position": "Senior Software Engineer",
                    "department": "Technology",
                    "email": "carol@company.com",
                    "hireDate": "2020-03-01",
                    "generation": 2
                }
            ),
            GraphNodeData(
                id="reports-to-2",
                type="connection",
                label="Reports To",
                data={
                    "connectionType": "employment",
                    "relationship": "reports-to",
                    "startDate": "2020-03-01",
                    "generation": 1.5
                }
            )
        ]
        
        edges = [
            GraphEdgeData(
                id="cto-reports-to-ceo",
                source="cto-bob",
                target="reports-to-1",
                type="employment"
            ),
            GraphEdgeData(
                id="reports-to-ceo",
                source="reports-to-1",
                target="ceo-alice",
                type="employment"
            ),
            GraphEdgeData(
                id="dev-reports-to-cto",
                source="dev-carol",
                target="reports-to-2",
                type="employment"
            ),
            GraphEdgeData(
                id="reports-to-cto",
                source="reports-to-2",
                target="cto-bob",
                type="employment"
            )
        ]
        
        return GraphResponse(nodes=nodes, edges=edges)
    
    raise HTTPException(status_code=404, detail="Company not found")

# Example: Social network graph
@router.get("/api/graph/social/{user_id}", response_model=GraphResponse)
async def get_social_graph(user_id: str):
    """
    Return social network as generic graph data.
    Shows friendships, mutual connections, etc.
    """
    
    if user_id == "john-doe":
        nodes = [
            GraphNodeData(
                id="john-doe",
                type="entity",
                label="John Doe",
                data={
                    "entityType": "person",
                    "name": "John Doe",
                    "username": "@johndoe",
                    "bio": "Software developer and coffee enthusiast",
                    "followers": 1250,
                    "following": 890,
                    "image": "/images/john-doe.jpg",
                    "generation": 0
                }
            ),
            GraphNodeData(
                id="jane-smith",
                type="entity",
                label="Jane Smith",
                data={
                    "entityType": "person",
                    "name": "Jane Smith",
                    "username": "@janesmith",
                    "bio": "UX Designer",
                    "mutualFriends": 15,
                    "generation": 1
                }
            ),
            GraphNodeData(
                id="friendship-1",
                type="connection",
                label="Friendship",
                data={
                    "connectionType": "friendship",
                    "since": "2018-05-12",
                    "mutualFriends": 15,
                    "generation": 0.5
                }
            )
        ]
        
        edges = [
            GraphEdgeData(
                id="john-friend-jane",
                source="john-doe",
                target="friendship-1",
                type="friendship"
            ),
            GraphEdgeData(
                id="friendship-to-jane",
                source="friendship-1",
                target="jane-smith",
                type="friendship"
            )
        ]
        
        return GraphResponse(nodes=nodes, edges=edges)
    
    raise HTTPException(status_code=404, detail="User not found")

# WebSocket endpoint for real-time updates
@router.websocket("/ws/graph/{graph_id}")
async def websocket_graph_updates(websocket, graph_id: str):
    """
    WebSocket endpoint for real-time graph updates.
    Sends new nodes/edges as they're added to the graph.
    """
    await websocket.accept()
    
    try:
        while True:
            # Listen for graph updates from your data source
            # Send updates to frontend in the same GraphResponse format
            
            # Example update message
            update = {
                "type": "node_added",
                "node": {
                    "id": "new-person",
                    "type": "entity",
                    "label": "New Person",
                    "data": {
                        "entityType": "person",
                        "name": "New Person",
                        "generation": 2
                    }
                }
            }
            
            await websocket.send_json(update)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Generic graph builder endpoint
@router.post("/api/graph/build", response_model=GraphResponse)
async def build_custom_graph(
    entities: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]]
):
    """
    Build a custom graph from provided entities and relationships.
    This allows dynamic graph creation from any data source.
    """
    
    nodes = []
    edges = []
    
    # Convert entities to nodes
    for i, entity in enumerate(entities):
        nodes.append(GraphNodeData(
            id=entity.get("id", f"entity-{i}"),
            type="entity",
            label=entity.get("name", entity.get("label", f"Entity {i}")),
            data={
                "entityType": entity.get("type", "default"),
                **entity,
                "generation": entity.get("generation", 0)
            }
        ))
    
    # Convert relationships to connection nodes and edges
    for i, rel in enumerate(relationships):
        connection_id = f"connection-{i}"
        
        # Create connection node
        nodes.append(GraphNodeData(
            id=connection_id,
            type="connection",
            label=rel.get("label", "Connection"),
            data={
                "connectionType": rel.get("type", "default"),
                **rel.get("metadata", {}),
                "generation": rel.get("generation", 0.5)
            }
        ))
        
        # Create edges
        edges.extend([
            GraphEdgeData(
                id=f"{rel['source']}-to-{connection_id}",
                source=rel["source"],
                target=connection_id,
                type=rel.get("type", "default")
            ),
            GraphEdgeData(
                id=f"{connection_id}-to-{rel['target']}",
                source=connection_id,
                target=rel["target"],
                type=rel.get("type", "default")
            )
        ])
    
    return GraphResponse(nodes=nodes, edges=edges)
