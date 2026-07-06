import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Routers
from app.routers import config as config_router
from app.routers.auth_db import get_current_user


def _admin_user():
    return {"id": "u1", "is_admin": True}


@pytest.fixture()
def app_client_config():
    app = FastAPI()
    app.include_router(config_router.router, prefix="/api")
    app.dependency_overrides[get_current_user] = _admin_user
    return TestClient(app)


def test_config_settings_contains_ta_keys(app_client_config: TestClient, monkeypatch):
    # Mock provider to return TA keys without hitting DB
    from app.services import config_provider as cfgprov

    async def _fake_eff():
        return {
            "ta_us_min_api_interval_seconds": 0.25,
            "ta_google_news_sleep_min_seconds": 1.5,
        }

    monkeypatch.setattr(cfgprov.provider, "get_effective_system_settings", _fake_eff)

    resp = app_client_config.get("/api/config/settings")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "ta_us_min_api_interval_seconds" in data
    assert data["ta_us_min_api_interval_seconds"] == 0.25
    assert data["ta_google_news_sleep_min_seconds"] == 1.5


def test_runtime_settings_priority_db_env_default(monkeypatch):
    # Ensure ENV is set
    monkeypatch.setenv("TA_US_MIN_API_INTERVAL_SECONDS", "3.0")

    # Monkeypatch provider to simulate DB value
    from app.services import config_provider as cfgprov
    from tradingagents.config import runtime_settings as rs

    async def _fake_eff_db():
        return {"ta_us_min_api_interval_seconds": 0.25}

    monkeypatch.setattr(cfgprov.provider, "get_effective_system_settings", _fake_eff_db)

    # DB should override ENV and default
    v_db = rs.get_float("TA_US_MIN_API_INTERVAL_SECONDS", "ta_us_min_api_interval_seconds", 1.0)
    assert abs(v_db - 0.25) < 1e-9

    # If DB doesn't provide the key, ENV should override default
    async def _fake_eff_empty():
        return {}

    monkeypatch.setattr(cfgprov.provider, "get_effective_system_settings", _fake_eff_empty)
    v_env = rs.get_float("TA_US_MIN_API_INTERVAL_SECONDS", "ta_us_min_api_interval_seconds", 1.0)
    assert abs(v_env - 3.0) < 1e-9

    # If ENV is absent too, fall back to default
    monkeypatch.delenv("TA_US_MIN_API_INTERVAL_SECONDS", raising=False)
    v_def = rs.get_float("TA_US_MIN_API_INTERVAL_SECONDS", "ta_us_min_api_interval_seconds", 1.0)
    assert abs(v_def - 1.0) < 1e-9

