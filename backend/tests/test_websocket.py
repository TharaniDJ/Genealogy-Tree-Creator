import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_websocket_connection():
    with client.websocket_connect("/ws") as websocket:
        assert websocket is not None

def test_websocket_send_receive():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"action": "get_relationships", "title": "Albert Einstein", "depth": 2})
        data = websocket.receive_json()
        assert "relationships" in data
        assert isinstance(data["relationships"], list)