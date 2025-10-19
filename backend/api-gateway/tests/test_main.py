from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "API Gateway running"


def test_proxy_unknown_service(client):
    response = client.get("/api/unknown/health")
    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_proxy_public_users_endpoint(monkeypatch, client):
    class DummyResponse:
        status_code = 200

        def __init__(self):
            self._json = {"ok": True}
            self.text = "ok"

        def json(self):
            return self._json

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def request(self, method, url, content=None, headers=None, params=None):
            DummyClient.captured = SimpleNamespace(method=method, url=url, headers=headers)
            return DummyResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", DummyClient)

    response = client.post("/api/users/login", json={"email": "user@example.com", "password": "secret"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert DummyClient.captured.url.endswith("/login")


def test_proxy_requires_token(monkeypatch, client):
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def request(self, *args, **kwargs):
            return SimpleNamespace(status_code=200, json=lambda: {}, text="{}")

    # Ensure token verification fails
    monkeypatch.setattr("app.main.verify_token", lambda header: None)
    monkeypatch.setattr("app.main.httpx.AsyncClient", DummyClient)

    response = client.get("/api/family/health")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_proxy_with_valid_token(monkeypatch, client):
    class DummyResponse:
        status_code = 200

        def __init__(self):
            self._json = {"status": "healthy"}
            self.text = "healthy"

        def json(self):
            return self._json

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def request(self, method, url, content=None, headers=None, params=None):
            return DummyResponse()

    monkeypatch.setattr("app.main.verify_token", lambda header: {"sub": "user"})
    monkeypatch.setattr("app.main.httpx.AsyncClient", DummyClient)

    response = client.get("/api/family/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
