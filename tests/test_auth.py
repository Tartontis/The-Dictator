from fastapi.testclient import TestClient

from backend.api.auth import get_settings
from backend.config import load_settings
from backend.main import app

client = TestClient(app)


def test_health_check_public():
    """Verify that /api/health is always public."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_public():
    """Verify that / is always public."""
    response = client.get("/")
    assert response.status_code == 200


def test_auth_not_enforced_when_no_key_configured(monkeypatch):
    """Verify that auth is not enforced when no API key is configured."""
    # Ensure settings has no api_key
    settings = load_settings()
    monkeypatch.setattr(settings.server, "api_key", None)

    # Override the shared get_settings dependency
    app.dependency_overrides[get_settings] = lambda: settings

    response = client.get("/api/config")
    assert response.status_code == 200

    app.dependency_overrides = {}


def test_auth_enforced_when_key_configured(monkeypatch):
    """Verify that auth is enforced when an API key is configured."""
    settings = load_settings()
    monkeypatch.setattr(settings.server, "api_key", "test-secret-key")

    # Override the shared get_settings dependency
    app.dependency_overrides[get_settings] = lambda: settings

    # Missing API key
    response = client.get("/api/config")
    assert response.status_code == 401
    assert response.json()["detail"] == "API Key missing"

    # Wrong API key
    response = client.get("/api/config", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Could not validate API Key"

    # Correct API key
    response = client.get("/api/config", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200

    app.dependency_overrides = {}
