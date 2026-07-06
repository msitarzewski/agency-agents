#!/usr/bin/env python3
"""
Minimal tests for:
1) SSE streaming endpoints: verify initial 'connected' event shape for task and batch streams
2) AnalysisWorker config intervals: verify ENV defaults and dynamic override application

These tests avoid touching real DB/Redis by mocking.
"""

import asyncio
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Import router and dependencies to override
from app.routers import sse as sse_router_mod
from app.routers.sse import router as sse_router
from app.routers.auth import get_current_user
from app.services.queue_service import QueueService, get_queue_service as real_get_queue_service


# ---------- Helpers / Fakes ----------
class FakePubSub:
    async def subscribe(self, channel: str):
        return None
    async def get_message(self, ignore_subscribe_messages: bool = True):
        await asyncio.sleep(0.01)
        return None
    async def unsubscribe(self, *channels):
        return None
    async def close(self):
        return None

class FakeRedis:
    def pubsub(self):
        return FakePubSub()

class FakeQueueService:
    async def get_task(self, task_id: str):
        return {"id": task_id, "user": "u1"}
    async def get_batch(self, batch_id: str):
        return {"id": batch_id, "user": "u1", "tasks": []}


def make_test_app(fake_queue_service: QueueService):
    app = FastAPI()
    # Attach SSE router under same prefix as production
    app.include_router(sse_router, prefix="/api/stream")

    # Override auth to a fixed user
    app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}

    # Override route-level queue service dependency used for pre-checks
    def _get_qsvc():
        return fake_queue_service
    app.dependency_overrides[real_get_queue_service] = _get_qsvc

    return app


# ---------- Tests: SSE ----------

def test_sse_task_connected_event(monkeypatch):
    # Monkeypatch Redis client inside module to our fake
    monkeypatch.setattr(sse_router_mod, "get_redis_client", lambda: FakeRedis())

    app = make_test_app(FakeQueueService())
    client = TestClient(app)

    with client.stream("GET", "/api/stream/tasks/T123") as resp:
        assert resp.status_code == 200
        # Read small chunk from stream and check the connected event
        chunk = next(resp.iter_lines())
        assert isinstance(chunk, (str, bytes))
        body = chunk.decode() if isinstance(chunk, (bytes, bytearray)) else chunk
        # The first line should be the SSE event name
        assert body.strip().startswith("event: connected")


def test_sse_batch_connected_event(monkeypatch):
    # Monkeypatch Redis client inside module to our fake
    monkeypatch.setattr(sse_router_mod, "get_redis_client", lambda: FakeRedis())
    # Also patch queue_service.get_redis_client because batch generator constructs
    # a QueueService via get_queue_service() inside the generator
    import app.services.queue_service as qsvc_mod
    monkeypatch.setattr(qsvc_mod, "get_redis_client", lambda: FakeRedis())

    app = make_test_app(FakeQueueService())
    client = TestClient(app)

    with client.stream("GET", "/api/stream/batches/B123") as resp:
        assert resp.status_code == 200
        chunk = next(resp.iter_lines())
        assert isinstance(chunk, (str, bytes))
        body = chunk.decode() if isinstance(chunk, (bytes, bytearray)) else chunk
        assert body.strip().startswith("event: connected")


# ---------- Tests: Worker config ----------

def test_worker_intervals_env_and_dynamic_override(monkeypatch):
    # Import in-scope to ensure monkeypatch targets the module objects
    import app.worker.analysis_worker as analysis_worker

    # Replace settings object with a lightweight dummy carrying needed fields
    class _DummySettings:
        WORKER_HEARTBEAT_INTERVAL = 30
        QUEUE_POLL_INTERVAL_SECONDS = 1.0
        QUEUE_CLEANUP_INTERVAL_SECONDS = 60.0
    monkeypatch.setattr(analysis_worker, "settings", _DummySettings())

    # Ensure start() does not touch real DB/Redis and finishes immediately
    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(analysis_worker, "init_database", noop)
    monkeypatch.setattr(analysis_worker, "init_redis", noop)
    monkeypatch.setattr(analysis_worker, "close_database", noop)
    monkeypatch.setattr(analysis_worker, "close_redis", noop, raising=False)

    # Make internal loops end instantly
    monkeypatch.setattr(analysis_worker.AnalysisWorker, "_work_loop", noop)
    monkeypatch.setattr(analysis_worker.AnalysisWorker, "_heartbeat_loop", noop)
    monkeypatch.setattr(analysis_worker.AnalysisWorker, "_cleanup_loop", noop)
    monkeypatch.setattr(analysis_worker.AnalysisWorker, "_cleanup", noop)

    # Provide a fake queue service object for attribute updates
    class _QS:
        user_concurrent_limit = 0
        global_concurrent_limit = 0
        visibility_timeout = 0
    monkeypatch.setattr(analysis_worker, "get_queue_service", lambda: _QS())

    # Dynamic overrides to be applied inside start()
    dynamic = {
        "worker_heartbeat_interval_seconds": 5,
        "queue_poll_interval_seconds": 0.2,
        "queue_cleanup_interval_seconds": 10,
        # also present but not asserted here
        "max_concurrent_tasks": 2,
        "default_analysis_timeout": 123,
    }
    async def _fake_eff():
        return dynamic
    monkeypatch.setattr(analysis_worker.config_provider, "get_effective_system_settings", _fake_eff, raising=False)

    # Instantiate with ENV values
    w = analysis_worker.AnalysisWorker(worker_id="wtest")
    assert w.heartbeat_interval == 30
    assert w.poll_interval == 1.0
    assert w.cleanup_interval == 60.0

    # Run start(), which should apply dynamic overrides and exit immediately
    asyncio.run(w.start())

    # Verify dynamic overrides took effect
    assert w.heartbeat_interval == 5
    assert abs(w.poll_interval - 0.2) < 1e-6
    assert w.cleanup_interval == 10

