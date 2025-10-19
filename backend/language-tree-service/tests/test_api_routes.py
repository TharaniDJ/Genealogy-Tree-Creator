from datetime import datetime
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.models.graph import GraphResponse
from app.models.language import LanguageRelationship, LanguageInfo


@pytest.fixture
def client(monkeypatch):
    async def fake_setup(*args, **kwargs):  # avoid real Mongo initialisation
        return None

    monkeypatch.setattr("app.services.graph_repository.graph_repo.setup", fake_setup)

    with TestClient(app) as test_client:
        yield test_client


def test_root_healthcheck(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "language-tree"


def test_relationships_endpoint(monkeypatch, client):
    sample = [
        {"language1": "English", "relationship": "parent", "language2": "Proto-Germanic"}
    ]

    async def fake_fetch(language_name, depth):
        return sample

    monkeypatch.setattr("app.api.routes.fetch_language_relationships", fake_fetch)

    response = client.get("/relationships/English/2")
    assert response.status_code == 200
    assert response.json() == sample


def test_relationships_depth_validation(client):
    response = client.get("/relationships/English/9")
    assert response.status_code == 400
    assert "Depth" in response.json()["detail"]


def test_distribution_map(monkeypatch, client):
    monkeypatch.setattr("app.api.routes.get_distribution_map_image", lambda qid: "http://example.com/map.png")
    response = client.get("/distribution-map/Q123")
    assert response.status_code == 200
    assert response.json()["image_url"] == "http://example.com/map.png"


def test_language_info(monkeypatch, client):
    info = LanguageInfo(speakers="Native", iso_code="en", distribution_map_url=None)

    async def fake_fetch(qid):
        return info

    monkeypatch.setattr("app.api.routes.fetch_language_info", fake_fetch)

    response = client.get("/info/Q1860")
    assert response.status_code == 200
    assert response.json()["iso_code"] == "en"


def test_save_graph(monkeypatch, client):
    payload = {
        "user_id": "user-1",
        "name": "English tree",
        "depth": 2,
        "node_count": 3,
        "relationships": [
            {"language1": "English", "relationship": "parent", "language2": "Proto-Germanic"}
        ]
    }

    graph_response = GraphResponse(
        id="abc123",
        user_id="user-1",
        name="English tree",
        depth=2,
        node_count=3,
        relationships=[LanguageRelationship(**payload["relationships"][0])],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    async def fake_save(graph):
        return graph_response

    monkeypatch.setattr("app.api.routes.graph_repo.save_graph", fake_save)

    response = client.post("/graphs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "English tree"
    assert body["relationships"][0]["language1"] == "English"


def test_get_graphs(monkeypatch, client):
    sample_graph = GraphResponse(
        id="abc123",
        user_id="user-1",
        name="English tree",
        depth=2,
        node_count=3,
        relationships=[LanguageRelationship(language1="English", relationship="parent", language2="Proto-Germanic")],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    async def fake_get_graphs(user_id):
        return [sample_graph]

    monkeypatch.setattr("app.api.routes.graph_repo.get_graphs_for_user", fake_get_graphs)

    response = client.get("/graphs/user-1")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "English tree"
