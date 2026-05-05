"""
Tests for API endpoints.
"""


def test_routes_import():
    """Verify API routes can be imported."""
    from backend.api.routes import router
    assert router is not None


def test_main_app_import():
    """Verify main app can be imported."""
    from backend.main import app
    assert app is not None
    assert app.title == "The Dictator"


def test_auth_no_key_configured():
    """Verify API works without auth when no key is configured."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.api.routes import get_settings
    from backend.config import Settings, ServerConfig, AudioConfig, TranscriptionConfig, VadConfig, SessionConfig, LLMConfig, ClusterConfig, TemplatesConfig
    from pathlib import Path

    # Mock settings with no api_key
    mock_settings = Settings(
        server=ServerConfig(api_key=None),
        audio=AudioConfig(),
        transcription=TranscriptionConfig(),
        vad=VadConfig(),
        session=SessionConfig(directory=Path("/tmp")),
        llm=LLMConfig(),
        cluster=ClusterConfig(),
        templates=TemplatesConfig(directory=Path("/tmp"))
    )

    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200

    response = client.get("/api/config")
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_auth_key_configured_success():
    """Verify API works with correct key when configured."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.api.routes import get_settings
    from backend.config import Settings, ServerConfig, AudioConfig, TranscriptionConfig, VadConfig, SessionConfig, LLMConfig, ClusterConfig, TemplatesConfig
    from pathlib import Path

    # Mock settings with api_key
    mock_settings = Settings(
        server=ServerConfig(api_key="secret"),
        audio=AudioConfig(),
        transcription=TranscriptionConfig(),
        vad=VadConfig(),
        session=SessionConfig(directory=Path("/tmp")),
        llm=LLMConfig(),
        cluster=ClusterConfig(),
        templates=TemplatesConfig(directory=Path("/tmp"))
    )

    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    # Health should be public
    response = client.get("/api/health")
    assert response.status_code == 200

    # Config should be protected
    response = client.get("/api/config", headers={"X-API-Key": "secret"})
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_auth_key_configured_failure():
    """Verify API rejects requests with wrong or missing key when configured."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.api.routes import get_settings
    from backend.config import Settings, ServerConfig, AudioConfig, TranscriptionConfig, VadConfig, SessionConfig, LLMConfig, ClusterConfig, TemplatesConfig
    from pathlib import Path

    # Mock settings with api_key
    mock_settings = Settings(
        server=ServerConfig(api_key="secret"),
        audio=AudioConfig(),
        transcription=TranscriptionConfig(),
        vad=VadConfig(),
        session=SessionConfig(directory=Path("/tmp")),
        llm=LLMConfig(),
        cluster=ClusterConfig(),
        templates=TemplatesConfig(directory=Path("/tmp"))
    )

    app.dependency_overrides[get_settings] = lambda: mock_settings
    client = TestClient(app)

    # Wrong key
    response = client.get("/api/config", headers={"X-API-Key": "wrong"})
    assert response.status_code == 403

    # Missing key
    response = client.get("/api/config")
    assert response.status_code == 403

    app.dependency_overrides.clear()
