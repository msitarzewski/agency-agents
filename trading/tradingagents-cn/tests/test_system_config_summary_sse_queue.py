import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Import the router and its dependency to override
from app.routers import system_config as system_cfg_router
from app.routers.auth import get_current_user


@pytest.fixture()
def app_client():
    app = FastAPI()
    app.include_router(system_cfg_router.router, prefix="/api/system")

    # Admin override
    def _admin_user():
        return {"id": "u1", "is_admin": True}

    app.dependency_overrides[get_current_user] = _admin_user

    client = TestClient(app)
    return client


def test_config_summary_contains_new_settings_fields(app_client: TestClient):
    resp = app_client.get("/api/system/config/summary")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "settings" in data
    s = data["settings"]

    # Queue/Worker
    assert "QUEUE_POLL_INTERVAL_SECONDS" in s
    assert "QUEUE_CLEANUP_INTERVAL_SECONDS" in s
    assert "WORKER_HEARTBEAT_INTERVAL" in s

    # SSE
    assert "SSE_POLL_TIMEOUT_SECONDS" in s
    assert "SSE_HEARTBEAT_INTERVAL_SECONDS" in s
    assert "SSE_TASK_MAX_IDLE_SECONDS" in s
    assert "SSE_BATCH_POLL_INTERVAL_SECONDS" in s
    assert "SSE_BATCH_MAX_IDLE_SECONDS" in s

