"""API tests for ``POST /alpha/compare`` + its SSE stream.

Deterministic by construction — no network, no flaky background-timing:

* **validation** runs through the real ``CompareRequest`` pydantic model via
  ``TestClient.post`` (rejection happens before any worker spawns);
* the **worker** (``_run_compare_blocking``) is called directly with
  ``compare_alphas`` stubbed, asserting job-state transitions and that an
  unexpected exception is sanitised (no path/message leak);
* the **stream** is exercised over a pre-seeded ``done`` job so the SSE
  generator emits ``result`` + ``done`` on the first pass and returns.

Loopback ``TestClient`` (127.0.0.1) bypasses dev-mode auth, matching the
convention in ``test_goal_api.py`` / ``test_security_auth_api.py``.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import api_server
from src.api import alpha_routes


def _client() -> TestClient:
    return TestClient(api_server.app, client=("127.0.0.1", 50000))


@pytest.fixture(autouse=True)
def _clear_compare_jobs():
    alpha_routes.ALPHA_COMPARE_JOBS.clear()
    yield
    alpha_routes.ALPHA_COMPARE_JOBS.clear()


_OK_ENVELOPE: dict[str, Any] = {
    "status": "ok",
    "universe": "csi300",
    "period": "2020-2025",
    "sort": "ir",
    "n_compared": 2,
    "n_skipped": 0,
    "winner": "alpha101_2",
    "ranking": [
        {"rank": 1, "id": "alpha101_2", "zoo": "alpha101", "ic_mean": 0.03,
         "ic_std": 0.05, "ir": 0.6, "ic_positive_ratio": 0.55, "ic_count": 200,
         "delta_ir_vs_best": 0.0},
        {"rank": 2, "id": "alpha101_1", "zoo": "alpha101", "ic_mean": 0.01,
         "ic_std": 0.05, "ir": 0.2, "ic_positive_ratio": 0.5, "ic_count": 200,
         "delta_ir_vs_best": -0.4},
    ],
    "skipped": [],
}


def _valid_body(**kw: Any) -> dict[str, Any]:
    body = {
        "alpha_ids": ["alpha101_1", "alpha101_2"],
        "universe": "csi300",
        "period": "2020-2025",
        "sort": "ir",
    }
    body.update(kw)
    return body


def _seed_job(job_id: str, **over: Any) -> dict[str, Any]:
    job = {
        "job_id": job_id, "status": "queued",
        "progress": {"n_done": 0, "n_total": 2, "current_alpha_id": None},
        "result": None, "error": None,
    }
    job.update(over)
    alpha_routes.ALPHA_COMPARE_JOBS[job_id] = job
    return job


# ── validation (pydantic, pre-worker) ───────────────────────────────────────


def test_compare_requires_two_ids() -> None:
    r = _client().post("/alpha/compare", json=_valid_body(alpha_ids=["alpha101_1"]))
    assert r.status_code == 422


def test_compare_dedupes_below_two_is_rejected() -> None:
    r = _client().post("/alpha/compare", json=_valid_body(alpha_ids=["alpha101_1", "alpha101_1"]))
    assert r.status_code == 422


def test_compare_rejects_unknown_universe() -> None:
    r = _client().post("/alpha/compare", json=_valid_body(universe="nasdaq"))
    assert r.status_code == 422


def test_compare_rejects_unknown_sort() -> None:
    r = _client().post("/alpha/compare", json=_valid_body(sort="sharpe"))
    assert r.status_code == 422


def test_compare_rejects_malformed_alpha_id() -> None:
    r = _client().post("/alpha/compare", json=_valid_body(alpha_ids=["alpha101_1", "BAD ID!"]))
    assert r.status_code == 422


# ── POST accepted ───────────────────────────────────────────────────────────


def test_compare_post_accepts_and_registers_job(monkeypatch) -> None:
    monkeypatch.setattr("src.factors.compare_runner.compare_alphas", lambda *a, **k: dict(_OK_ENVELOPE))
    r = _client().post("/alpha/compare", json=_valid_body())
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "ok"
    assert body["job_id"] in alpha_routes.ALPHA_COMPARE_JOBS


# ── worker (_run_compare_blocking) ──────────────────────────────────────────


def test_worker_stores_ok_envelope(monkeypatch) -> None:
    monkeypatch.setattr("src.factors.compare_runner.compare_alphas", lambda *a, **k: dict(_OK_ENVELOPE))
    _seed_job("aaaa1111")
    alpha_routes._run_compare_blocking("aaaa1111", ["alpha101_1", "alpha101_2"], "csi300", "2020-2025", "ir")
    job = alpha_routes.ALPHA_COMPARE_JOBS["aaaa1111"]
    assert job["status"] == "done"
    assert job["result"]["winner"] == "alpha101_2"
    assert job["result"]["ranking"][0]["id"] == "alpha101_2"


def test_worker_marks_error_envelope(monkeypatch) -> None:
    err = {"status": "error", "error": "no requested alphas could be evaluated",
           "ranking": [], "skipped": [{"id": "x", "reason": "unknown"}]}
    monkeypatch.setattr("src.factors.compare_runner.compare_alphas", lambda *a, **k: err)
    _seed_job("bbbb2222")
    alpha_routes._run_compare_blocking("bbbb2222", ["x", "y"], "csi300", "2020-2025", "ir")
    job = alpha_routes.ALPHA_COMPARE_JOBS["bbbb2222"]
    assert job["status"] == "error"
    assert "evaluated" in job["error"]


def test_worker_sanitises_unexpected_exception(monkeypatch) -> None:
    def _boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise RuntimeError("leak: /etc/secret/path token=abc123")

    monkeypatch.setattr("src.factors.compare_runner.compare_alphas", _boom)
    _seed_job("cccc3333")
    alpha_routes._run_compare_blocking("cccc3333", ["x", "y"], "csi300", "2020-2025", "ir")
    job = alpha_routes.ALPHA_COMPARE_JOBS["cccc3333"]
    assert job["status"] == "error"
    # No raw message / path leaks to the client-facing error string.
    assert job["error"] == "internal error; see server logs"


# ── result projector ────────────────────────────────────────────────────────


def test_result_projector_drops_status_keeps_ranking() -> None:
    wire = alpha_routes._compare_result_for_wire(dict(_OK_ENVELOPE))
    assert "status" not in wire
    assert wire["winner"] == "alpha101_2"
    assert wire["ranking"][0]["id"] == "alpha101_2"


# ── SSE stream ──────────────────────────────────────────────────────────────


def test_stream_emits_result_then_done() -> None:
    _seed_job(
        "dddd4444",
        status="done",
        progress={"n_done": 2, "n_total": 2, "current_alpha_id": "alpha101_2"},
        result=dict(_OK_ENVELOPE),
    )
    with _client() as client:
        r = client.get("/alpha/compare/dddd4444/stream")
        assert r.status_code == 200
        text = r.text
    assert "event: result" in text
    assert "event: done" in text
    assert "ranking" in text
    assert "alpha101_2" in text


def test_stream_unknown_job_is_404() -> None:
    r = _client().get("/alpha/compare/abcdef123456/stream")
    assert r.status_code == 404


def test_stream_invalid_job_id_is_400() -> None:
    r = _client().get("/alpha/compare/bad@id/stream")
    assert r.status_code == 400
