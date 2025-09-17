from __future__ import annotations

from typing import List, Optional
from datetime import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ReturnDocument
from bson import ObjectId

from app.models.graph import GraphSaveRequest, GraphResponse, GraphUpdateRequest


MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Genealogy_Tree_Creator"
COLLECTION_NAME = "Language_Trees"


def _to_graph_response(doc: dict) -> GraphResponse:
    return GraphResponse(
        id=str(doc.get("_id")) if doc.get("_id") else doc.get("id", ""),
        user_id=doc["user_id"],
        name=doc["name"],
        depth=doc["depth"],
        node_count=doc["node_count"],
        relationships=doc["relationships"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class GraphRepository:
    """MongoDB-backed repository using Motor."""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._collection: Optional[AsyncIOMotorCollection] = None

    async def setup(self, uri: str = MONGO_URI, db_name: str = DB_NAME, collection_name: str = COLLECTION_NAME):
        self._client = AsyncIOMotorClient(uri)
        db = self._client[db_name]
        self._collection = db[collection_name]
        # Index to ensure fast lookups and unique per-user name
        try:
            await self._collection.create_index(
                [("user_id", 1), ("name", 1)],
                unique=True,
                name="user_name_unique",
            )
        except Exception:
            pass

    async def save_graph(self, payload: GraphSaveRequest) -> GraphResponse:
        assert self._collection is not None, "Repository not initialized. Call setup() at startup."
        now = datetime.utcnow()
        doc = {
            "user_id": payload.user_id or "1234",
            "name": payload.name,
            "depth": payload.depth,
            "node_count": payload.node_count,
            "relationships": [r.model_dump() for r in payload.relationships],
            "created_at": now,
            "updated_at": now,
        }
        # Upsert by (user_id, name)
        result = await self._collection.find_one_and_update(
            {"user_id": doc["user_id"], "name": doc["name"]},
            {"$set": doc},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            # Some drivers may return None for upsert; fetch explicitly
            result = await self._collection.find_one({"user_id": doc["user_id"], "name": doc["name"]})
        return _to_graph_response(result)

    async def get_graphs_for_user(self, user_id: str) -> List[GraphResponse]:
        assert self._collection is not None
        cursor = self._collection.find({"user_id": user_id}).sort("updated_at", -1)
        results: List[GraphResponse] = []
        async for doc in cursor:
            results.append(_to_graph_response(doc))
        return results

    async def get_graph_by_name(self, user_id: str, name: str) -> Optional[GraphResponse]:
        assert self._collection is not None
        doc = await self._collection.find_one({"user_id": user_id, "name": name})
        return _to_graph_response(doc) if doc else None

    async def update_graph(self, user_id: str, name: str, update: GraphUpdateRequest) -> Optional[GraphResponse]:
        assert self._collection is not None
        updates = {k: v for k, v in update.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            # Touch updated_at
            updates = {}
        updates["updated_at"] = datetime.utcnow()
        # Handle rename carefully
        query = {"user_id": user_id, "name": name}
        if "name" in updates and updates["name"] != name:
            # Ensure no conflict
            existing = await self._collection.find_one({"user_id": user_id, "name": updates["name"]})
            if existing:
                # Overwrite policy could be defined; for now, treat as conflict
                raise ValueError("Graph with the new name already exists")
        if "relationships" in updates and isinstance(updates["relationships"], list):
            updates["relationships"] = [r if isinstance(r, dict) else r.model_dump() for r in updates["relationships"]]
        result = await self._collection.find_one_and_update(
            query,
            {"$set": updates},
            return_document=True
        )
        return _to_graph_response(result) if result else None

    async def delete_graph(self, user_id: str, name: str) -> bool:
        assert self._collection is not None
        res = await self._collection.delete_one({"user_id": user_id, "name": name})
        return res.deleted_count > 0


# Singleton repo instance for simple usage via import
graph_repo = GraphRepository()
