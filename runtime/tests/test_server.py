"""FastAPI endpoint tests. Uses the TestClient — no network calls."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agency.server import build_app


def test_api_skills_returns_count_and_list():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    assert all({"slug", "name", "category", "description", "emoji"} <= set(s) for s in data["skills"][:3])


def test_api_plan_falls_back_to_keyword_match_without_api_key(monkeypatch):
    # Force _maybe_llm to return None so the planner takes the offline path.
    from agency import server as server_mod
    monkeypatch.setattr(server_mod, "_maybe_llm", lambda: None)

    app = build_app()
    client = TestClient(app)
    resp = client.post("/api/plan", json={"message": "build me a React component"})
    assert resp.status_code == 200
    data = resp.json()
    assert "skill" in data
    assert "slug" in data["skill"] and "name" in data["skill"]
    assert data["candidates"]


def test_api_run_returns_503_when_no_api_key(monkeypatch):
    from agency import server as server_mod
    from agency.llm import LLMError

    def _boom() -> None:
        raise LLMError("ANTHROPIC_API_KEY not set")
    monkeypatch.setattr(server_mod, "_require_llm", _boom)

    app = build_app()
    client = TestClient(app)
    resp = client.post("/api/run", json={"message": "anything"})
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.text


def test_api_run_stream_returns_503_when_no_api_key(monkeypatch):
    from agency import server as server_mod
    from agency.llm import LLMError

    def _boom() -> None:
        raise LLMError("ANTHROPIC_API_KEY not set")
    monkeypatch.setattr(server_mod, "_require_llm", _boom)

    app = build_app()
    client = TestClient(app)
    resp = client.post("/api/run/stream", json={"message": "anything"})
    assert resp.status_code == 503


def test_index_serves_html():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Agency" in resp.text
    assert "/api/run/stream" in resp.text  # UI talks to the streaming endpoint
