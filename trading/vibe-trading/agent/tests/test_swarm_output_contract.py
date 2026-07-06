"""Regression tests for P01 + P03 — swarm output contract.

A worker that produced no substantive deliverable (plan-only stub, mock
data, unparsed tool markup, raw tool envelope, or a data agent that made no
tool call and wrote no report) must NOT be reported ``completed``, and the
runtime must not fold ``timeout`` / ``token_limit`` / ``incomplete`` into a
successful run.

The ``test_timeout_terminal_*`` runtime test is the fail-before / pass-after
anchor: on the pre-fix code ``timeout`` was mapped to ``completed`` so the run
reported success; post-fix it is a failure. The content-contract unit tests
pin the new ``_classify_deliverable`` policy (Hybrid: content-sanity for all
agents, tool-evidence only for data agents — tool-less synthesis/editor roles
are intentionally NOT failed).
"""

from __future__ import annotations

import threading
from pathlib import Path

from src.swarm.models import (
    RunStatus,
    SwarmAgentSpec,
    SwarmRun,
    SwarmTask,
    WorkerResult,
)
from src.swarm.store import SwarmStore
from src.swarm.worker import (
    _classify_deliverable,
    _is_data_agent,
    _is_error_result,
    _report_written,
)
import src.swarm.runtime as rt

PLAN_STUB = (
    "### Phase 1 — Plan\n"
    "1. Load the asset-allocation skill\n"
    "2. Fetch data\n\n"
    "### Phase 2 — Execute\n"
    "First, I'll load the necessary skills."
)
REAL_REPORT = (
    "# BTC-USDT — Short-Term View\n\n"
    "Spot fetched via okx: 81,704.6 (2026-05-05). 7d range 77,750–82,842.\n\n"
    "**Recommendation: accumulate on dips to 79k; invalidation below 77.5k.**\n"
    "Position 3% NAV, stop 76,900, target 86,000. Funding 0.035%/8h is elevated\n"
    "but not extreme; on-chain exchange reserves declining (bullish)."
)


# ---- content contract (Hybrid policy) -------------------------------------
def test_plan_only_is_rejected():
    assert _classify_deliverable(PLAN_STUB, is_data_agent=True, report_written=False, data_tool_calls=0)


def test_unparsed_tool_markup_is_rejected():
    txt = "<｜tool▁calls▁begin｜>function<tool_sep>load_skill"
    assert _classify_deliverable(txt, is_data_agent=False, report_written=False, data_tool_calls=0)


def test_mock_data_is_rejected():
    txt = "### Risk Audit (Mock Data)\nWorst Drawdown: -23.5% | 95% VaR: -4.2%"
    assert _classify_deliverable(txt, is_data_agent=True, report_written=True, data_tool_calls=3)


def test_raw_tool_envelope_is_rejected():
    txt = '{"status": "ok", "content": "<skill name=technical-basic>...</skill>"}'
    assert _classify_deliverable(txt, is_data_agent=False, report_written=False, data_tool_calls=1)


def test_data_agent_without_evidence_is_rejected():
    assert _classify_deliverable(REAL_REPORT, is_data_agent=True, report_written=False, data_tool_calls=0)


def test_synthesis_agent_prose_is_accepted():
    """FALSE-REJECT GUARD: a tool-less synthesis/editor agent that produced
    real prose with no tool calls and no report.md must pass."""
    assert _classify_deliverable(REAL_REPORT, is_data_agent=False, report_written=False, data_tool_calls=0) is None


def test_real_report_is_accepted():
    assert _classify_deliverable(REAL_REPORT, is_data_agent=True, report_written=True, data_tool_calls=5) is None


def test_is_data_agent_classification():
    synth = SwarmAgentSpec(id="editor", role="Editor", system_prompt="x", tools=["bash", "read_file", "write_file"])
    analyst = SwarmAgentSpec(
        id="onchain", role="On-Chain", system_prompt="x", tools=["bash", "write_file", "get_market_data"]
    )
    assert _is_data_agent(synth) is False
    assert _is_data_agent(analyst) is True


def test_report_written_detection(tmp_path: Path):
    assert _report_written(tmp_path) is False
    (tmp_path / "report.md").write_text("   \n ", encoding="utf-8")
    assert _report_written(tmp_path) is False
    (tmp_path / "report.md").write_text("# Real report\nbuy.", encoding="utf-8")
    assert _report_written(tmp_path) is True


# ---- runtime integrity ----------------------------------------------------
def _run(tmp_path: Path, worker_result: WorkerResult) -> SwarmRun:
    store = SwarmStore(base_dir=tmp_path)
    runtime = rt.SwarmRuntime(store=store)
    agent = SwarmAgentSpec(id="analyst", role="Analyst", system_prompt="x", max_retries=0)
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="do x")
    run = SwarmRun(id="r", preset_name="demo", created_at="2026-01-01T00:00:00Z", agents=[agent], tasks=[task])
    store.create_run(run)
    runtime._execute_run(run, threading.Event())
    reloaded = store.load_run(run.id)
    assert reloaded is not None
    return reloaded


def test_timeout_terminal_run_not_completed(tmp_path, monkeypatch):
    """fail-before / pass-after anchor: timeout terminal must not be a success."""
    monkeypatch.setattr(
        rt,
        "run_worker",
        lambda *a, **k: WorkerResult(status="timeout", summary="partial work"),
    )
    run = _run(tmp_path, None)
    assert run.status != RunStatus.completed
    assert run.final_report is None


def test_incomplete_terminal_run_not_completed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        rt,
        "run_worker",
        lambda *a, **k: WorkerResult(
            status="incomplete",
            summary=PLAN_STUB,
            error="output contract not met: plan-only stub",
        ),
    )
    run = _run(tmp_path, None)
    assert run.status != RunStatus.completed
    assert run.final_report is None
    assert run.tasks[0].error and "plan-only" in run.tasks[0].error


def test_genuine_completion_still_succeeds(tmp_path, monkeypatch):
    """Guard: a real deliverable must still complete and become final_report."""
    monkeypatch.setattr(
        rt,
        "run_worker",
        lambda *a, **k: WorkerResult(status="completed", summary=REAL_REPORT, iterations=4),
    )
    run = _run(tmp_path, None)
    assert run.status == RunStatus.completed
    assert run.final_report == REAL_REPORT


# ---- _is_error_result: JSON parse + truncation fallback -------------------
# Follow-up from #119: the substring head-match could (a) false-positive on
# a nested ``status`` field and (b) false-negate when the envelope sat past
# the 160-char head. Parsing the envelope as JSON pins both.


def test_is_error_result_top_level_error():
    assert _is_error_result('{"status": "error", "error": "bad key"}') is True
    assert _is_error_result('{"status":"error"}') is True


def test_is_error_result_top_level_ok():
    assert _is_error_result('{"status": "ok", "content": "..."}') is False


def test_is_error_result_nested_error_no_false_positive():
    """A nested ``status`` (e.g. inside ``data``) must NOT count — only the
    envelope status matters for the deliverable contract."""
    nested = '{"status": "ok", "data": {"status": "error", "detail": "x"}}'
    assert _is_error_result(nested) is False


def test_is_error_result_error_past_substring_head():
    """G2: an error envelope where ``status`` sits past the 160-char head
    (long preamble in another field). Substring head-match used to miss
    this; JSON parse catches it."""
    long_field = "x" * 200
    payload = '{"meta": "' + long_field + '", "status": "error"}'
    assert _is_error_result(payload) is True


def test_is_error_result_truncated_falls_back_to_substring():
    """Truncated / unparseable JSON still gets the original substring
    classifier; the function must never raise on the worker hot path."""
    truncated = '{"status": "error", "trace": "...'  # missing closing quote
    assert _is_error_result(truncated) is True


def test_is_error_result_non_json_safe():
    assert _is_error_result("") is False
    assert _is_error_result(None) is False  # type: ignore[arg-type]
    assert _is_error_result("plain text output") is False
    assert _is_error_result("[1, 2, 3]") is False  # JSON array, not envelope


def test_is_error_result_other_status_values():
    """Only ``"error"`` counts; ``"warning"`` / ``"degenerate"`` etc. are
    not error envelopes (the worker still credits them as a tool call)."""
    assert _is_error_result('{"status": "degenerate", "warning": "T=0"}') is False
    assert _is_error_result('{"status": "warning"}') is False
