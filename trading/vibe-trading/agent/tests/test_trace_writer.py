"""TraceWriter offload and path-safety tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.agent.trace as trace_mod
from src.agent.trace import TraceWriter


def _raw_entries(trace_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (trace_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_tool_result_offload_uses_safe_name_and_resolves_only_on_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Large tool results should not trust provider-supplied call IDs as paths."""
    monkeypatch.setattr(trace_mod, "TOOL_RESULT_OFFLOAD_THRESHOLD", 8)
    trace = TraceWriter(tmp_path)

    trace.write_tool_result(
        call_id="../escape/token",
        result="large result body",
        tool_name="danger_tool",
        status="ok",
        elapsed_ms=12,
        iteration=3,
    )
    trace.close()

    [entry] = _raw_entries(tmp_path)
    assert "result" not in entry
    assert entry["preview"] == "large result body"[: trace_mod.OFFLOAD_PREVIEW_CHARS]
    assert entry["result_preview"] == entry["preview"]
    assert entry["result_size"] == len("large result body")
    assert entry["result_path"].startswith("tool-results/")
    assert ".." not in Path(entry["result_path"]).parts
    assert Path(entry["result_path"]).name == Path(entry["result_path"]).as_posix().split("/")[-1]
    assert not (tmp_path.parent / "escape" / "token").exists()

    unresolved = TraceWriter.read(tmp_path)
    assert "result" not in unresolved[0]

    resolved = TraceWriter.read(tmp_path, resolve_offloads=True)
    assert resolved[0]["result"] == "large result body"


def test_trace_reader_refuses_offload_path_escape(tmp_path: Path) -> None:
    """A malicious trace.jsonl must not make read() open files outside trace dir."""
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("do-not-read", encoding="utf-8")
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    (trace_dir / "trace.jsonl").write_text(
        json.dumps(
            {
                "type": "tool_result",
                "iter": 1,
                "tool": "ghost",
                "result_path": "../secret.txt",
                "result_preview": "x",
                "result_size": 11,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    [entry] = TraceWriter.read(trace_dir, resolve_offloads=True)

    assert "result" not in entry


def test_text_field_offload_round_trips_selected_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Long prompt/answer fields can be offloaded without forcing all blobs open."""
    monkeypatch.setattr(trace_mod, "TRACE_TEXT_OFFLOAD_THRESHOLD", 8)
    trace = TraceWriter(tmp_path)
    trace.write_text_entry(
        {"type": "answer", "iter": 1},
        field="content",
        value="long final answer",
        offload_kind="answer",
    )
    trace.close()

    unresolved = TraceWriter.read(tmp_path)
    assert "content" not in unresolved[0]
    assert unresolved[0]["content_preview"] == "long final answer"[: trace_mod.OFFLOAD_PREVIEW_CHARS]

    still_unresolved = TraceWriter.read(
        tmp_path,
        resolve_offloads=True,
        resolve_fields={"result"},
    )
    assert "content" not in still_unresolved[0]

    resolved = TraceWriter.read(
        tmp_path,
        resolve_offloads=True,
        resolve_fields={"content"},
    )
    assert resolved[0]["content"] == "long final answer"


def test_find_trace_dir_prefers_sessions_then_runs(tmp_path: Path) -> None:
    """Session traces are preferred while legacy run traces still work."""
    sessions = tmp_path / "sessions"
    runs = tmp_path / "runs"
    session_dir = sessions / "abc"
    run_dir = runs / "abc"
    session_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    (session_dir / "trace.jsonl").write_text('{"type":"session"}\n', encoding="utf-8")
    (run_dir / "trace.jsonl").write_text('{"type":"run"}\n', encoding="utf-8")

    assert TraceWriter.find_trace_dir("abc", runs_dir=runs, sessions_dir=sessions) == session_dir
    assert TraceWriter.find_trace_dir("missing", runs_dir=runs, sessions_dir=sessions) is None
