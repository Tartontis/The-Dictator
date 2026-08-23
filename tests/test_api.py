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
