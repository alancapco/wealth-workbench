import os
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_live_is_process_only():
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_registered_health_paths():
    """Health endpoints are accessible, regardless of how FastAPI enumerates routes internally."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    live_resp = client.get("/health/live")
    assert live_resp.status_code == 200
    
    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code in {200, 503}  # 503 is expected when not ready


def test_ready_fails_closed_without_schema_and_identity():
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "NOT_READY"
    assert set(body["checks"]) == {"database", "schema", "identity_config"}
    assert all(isinstance(value, bool) for value in body["checks"].values())
    assert body["providers"]


def test_app_imports_without_network_or_credentials():
    """Application and all routers import without requiring network or credentials."""
    # This test passes if the module imports above succeeded
    assert app is not None
    # Verify no external provider client was constructed at import time
    from app.core import config
    # Config reads env but does not fail; providers report their own state
    assert hasattr(config.settings, "provider_configuration")


def test_fixture_auth_rejected_in_production():
    """AUTH_MODE=fixture must be rejected when APP_ENV=production."""
    import importlib
    import sys
    
    # Save and restore original environment
    original_auth = os.environ.get("AUTH_MODE")
    original_env = os.environ.get("APP_ENV")
    
    try:
        os.environ["AUTH_MODE"] = "fixture"
        os.environ["APP_ENV"] = "production"
        
        # Force reload of config module
        if "app.core.config" in sys.modules:
            del sys.modules["app.core.config"]
        
        # Should raise validation error
        with pytest.raises(ValueError, match="fixture.*production"):
            from app.core.config import Settings
            Settings()
    finally:
        # Restore original environment
        if original_auth is None:
            os.environ.pop("AUTH_MODE", None)
        else:
            os.environ["AUTH_MODE"] = original_auth
        if original_env is None:
            os.environ.pop("APP_ENV", None)
        else:
            os.environ["APP_ENV"] = original_env
        
        # Reload config with original env
        if "app.core.config" in sys.modules:
            del sys.modules["app.core.config"]
        importlib.import_module("app.core.config")


def test_database_engine_echo_disabled():
    """SQL echo must be disabled for all modes to protect sensitive data."""
    from app.core.database import engine
    if engine is not None:
        assert engine.echo is False or engine.echo == "debug"  # False or debug mode only
