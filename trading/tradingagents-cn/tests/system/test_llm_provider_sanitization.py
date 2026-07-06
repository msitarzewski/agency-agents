import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.routers import config as config_router  # noqa: E402
from app.routers.auth import get_current_user  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.config_service import config_service  # noqa: E402


@pytest.fixture()
def test_app():
    app = FastAPI()
    app.include_router(config_router.router, prefix="/api")

    # Override auth dependency
    def _fake_user():
        return User(username="tester", email="t@example.com", hashed_password="x")

    app.dependency_overrides[get_current_user] = _fake_user

    with TestClient(app) as client:
        yield client


def test_add_llm_provider_sanitizes_api_key(monkeypatch, test_app: TestClient):
    captured = {}

    async def mock_add_llm_provider(provider):
        captured["api_key"] = provider.api_key
        return "mock-id-123"

    monkeypatch.setattr(config_service, "add_llm_provider", mock_add_llm_provider)

    payload = {
        "name": "openai",
        "display_name": "OpenAI",
        "description": "desc",
        "website": "https://openai.com",
        "api_doc_url": None,
        "logo_url": None,
        "is_active": True,
        "supported_features": [],
        "default_base_url": None,
        "api_key": "SHOULD_BE_STRIPPED",
        "api_secret": None,
        "extra_config": {}
    }

    resp = test_app.post("/api/config/llm/providers", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("success") is True
    # Ensure api_key passed to service was sanitized to empty string
    assert captured.get("api_key") == ""


def test_update_llm_provider_sanitizes_api_key(monkeypatch, test_app: TestClient):
    captured = {}

    async def mock_update_llm_provider(provider_id, update_data):
        captured["provider_id"] = provider_id
        captured["api_key"] = update_data.get("api_key")
        return True

    monkeypatch.setattr(config_service, "update_llm_provider", mock_update_llm_provider)

    payload = {
        "name": "openai",
        "display_name": "OpenAI",
        "description": "desc",
        "website": "https://openai.com",
        "api_doc_url": None,
        "logo_url": None,
        "is_active": True,
        "supported_features": [],
        "default_base_url": None,
        "api_key": "SHOULD_BE_STRIPPED",
        "api_secret": None,
        "extra_config": {"k": "v"}
    }

    resp = test_app.put("/api/config/llm/providers/abc123", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("success") is True
    assert captured.get("provider_id") == "abc123"
    # Ensure api_key in update_data was sanitized to empty string
    assert captured.get("api_key") == ""

