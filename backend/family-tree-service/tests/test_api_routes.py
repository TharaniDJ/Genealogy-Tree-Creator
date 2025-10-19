import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client(monkeypatch):
    # Prevent background Gemini calls in tests.
    monkeypatch.setattr("app.services.relationship_classifier.classify_relationships", lambda relationships: relationships, raising=False)
    with TestClient(app) as test_client:
        yield test_client


def test_root_healthcheck(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is Working"}


def test_get_relationships_uses_service(monkeypatch, client):
    sample = [
        {"entity1": "Alice", "relationship": "child of", "entity2": "Bob"},
        {"entity1": "Alice", "relationship": "sibling of", "entity2": "Charlie"},
    ]

    async def fake_fetch(page_title, depth, websocket_manager=None):
        return sample

    monkeypatch.setattr("app.api.routes.fetch_relationships", fake_fetch)

    response = client.get("/relationships/Alice/2")
    assert response.status_code == 200
    assert response.json() == sample


def test_expand_by_qid_happy_path(monkeypatch, client):
    sample = [
        {"entity1": "Alice", "relationship": "child of", "entity2": "Bob"}
    ]

    async def fake_expand(**kwargs):
        return sample

    monkeypatch.setattr("app.api.routes.fetch_relationships_by_qid", fake_expand)

    payload = {"qid": "Q123", "depth": 2, "entity_name": "Alice"}
    response = client.post("/expand-by-qid", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["relationships"] == sample


def test_expand_by_qid_missing_qid(client):
    response = client.post("/expand-by-qid", json={"depth": 2})
    assert response.status_code == 200
    assert response.json() == {"error": "QID is required"}


def test_classify_relationships_endpoint(monkeypatch, client):
    sample_response = [
        {"entity1": "Dana", "relationship": "child of", "entity2": "Eli", "classification": "BIOLOGICAL"}
    ]

    async def fake_thread_runner(func, relationships):
        return sample_response

    monkeypatch.setattr(asyncio, "to_thread", fake_thread_runner)

    payload = {"relationships": [{"entity1": "Dana", "relationship": "child of", "entity2": "Eli"}]}
    response = client.post("/classify-relationships", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["total"] == 1
    assert body["relationships"] == sample_response
