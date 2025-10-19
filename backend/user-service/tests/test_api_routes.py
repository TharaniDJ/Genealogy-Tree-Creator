from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_healthcheck(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "User service is running"


def test_register_success(monkeypatch, client):
    async def fake_get_user_by_email(email):  # email available
        return None

    async def fake_create_user(user_in):
        return {
            "id": "user-1",
            "email": user_in.email,
            "full_name": user_in.full_name,
        }

    monkeypatch.setattr("app.api.routes.crud.get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr("app.api.routes.crud.create_user", fake_create_user)

    payload = {"email": "new@example.com", "full_name": "New User", "password": "secret123"}
    response = client.post("/api/users/register", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New User"


def test_register_duplicate_email(monkeypatch, client):
    async def fake_get_user_by_email(email):
        return {"_id": "existing", "email": email, "full_name": "Existing"}

    monkeypatch.setattr("app.api.routes.crud.get_user_by_email", fake_get_user_by_email)

    payload = {"email": "existing@example.com", "full_name": "Existing", "password": "secret"}
    response = client.post("/api/users/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(monkeypatch, client):
    async def fake_authenticate(email, password):
        return {"_id": "user-id", "id": "user-id", "email": email, "full_name": "Tester"}

    def fake_create_token(data, expires_delta=None):
        return "token123"

    monkeypatch.setattr("app.api.routes.authenticate_user", fake_authenticate)
    monkeypatch.setattr("app.api.routes.create_access_token", fake_create_token)

    payload = {"email": "user@example.com", "password": "secret"}
    response = client.post("/api/users/login", json=payload)
    assert response.status_code == 200
    assert response.json()["access_token"] == "token123"


def test_login_invalid_credentials(monkeypatch, client):
    async def fake_authenticate(email, password):
        return None

    monkeypatch.setattr("app.api.routes.authenticate_user", fake_authenticate)

    payload = {"email": "user@example.com", "password": "wrong"}
    response = client.post("/api/users/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
