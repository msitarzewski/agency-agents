"""Tests for AgentLoop pure helper functions (zero LLM dependency)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.agent.loop import (
    KEEP_RECENT,
    COLLAPSE_PRESERVE_RECENT,
    COLLAPSE_TEXT_MIN,
    MICROCOMPACT_THRESHOLD,
    estimate_tokens,
    _microcompact,
    _context_collapse,
    _fix_tool_pairs,
    _is_tool_success,
    _normalize_tool_run_dir,
)


def _apply_microcompact_gate(messages: list) -> None:
    """Mirror AgentLoop layer-1 gate (``loop.py`` ~572-573)."""
    if estimate_tokens(messages) > MICROCOMPACT_THRESHOLD:
        _microcompact(messages)


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_empty(self) -> None:
        assert estimate_tokens([]) == len("[]") // 4

    def test_proportional(self) -> None:
        short = [{"role": "user", "content": "hi"}]
        long = [{"role": "user", "content": "x" * 4000}]
        assert estimate_tokens(long) > estimate_tokens(short)

    def test_rough_accuracy(self) -> None:
        # ~4 chars per token
        msg = [{"role": "user", "content": "a" * 400}]
        tokens = estimate_tokens(msg)
        # Should be roughly 100 tokens for 400 chars of content (plus overhead)
        assert 80 < tokens < 200


# ---------------------------------------------------------------------------
# _microcompact
# ---------------------------------------------------------------------------


class TestMicrocompact:
    def test_clears_old_tool_messages(self) -> None:
        messages = [
            {"role": "system", "content": "system"},
        ]
        # Add KEEP_RECENT + 5 tool messages with long content
        for i in range(KEEP_RECENT + 5):
            messages.append({"role": "tool", "content": f"{'x' * 200} result_{i}", "tool_call_id": f"tc_{i}"})

        _microcompact(messages)

        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        # Old ones should be [cleared]
        cleared = [m for m in tool_msgs if m["content"] == "[cleared]"]
        preserved = [m for m in tool_msgs if m["content"] != "[cleared]"]
        assert len(cleared) == 5
        assert len(preserved) == KEEP_RECENT

    def test_preserves_short_content(self) -> None:
        messages = [
            {"role": "tool", "content": "short", "tool_call_id": "tc_0"},
            {"role": "tool", "content": "also short", "tool_call_id": "tc_1"},
            {"role": "tool", "content": "short too", "tool_call_id": "tc_2"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_3"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_4"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_5"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_6"},
        ]
        _microcompact(messages)
        # First tool msg is old and long enough → cleared
        # But "short" is ≤100 chars → not cleared even if old
        short_msgs = [m for m in messages if m["content"] in ("short", "also short")]
        assert len(short_msgs) == 2

    def test_no_op_when_few_messages(self) -> None:
        messages = [
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_0"},
        ]
        _microcompact(messages)
        assert messages[0]["content"] != "[cleared]"

    def test_does_not_touch_non_tool(self) -> None:
        messages = [
            {"role": "user", "content": "x" * 500},
            {"role": "assistant", "content": "x" * 500},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_0"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_1"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_2"},
            {"role": "tool", "content": "x" * 200, "tool_call_id": "tc_3"},
        ]
        _microcompact(messages)
        assert messages[0]["content"] == "x" * 500
        assert messages[1]["content"] == "x" * 500


class TestMicrocompactThresholdGate:
    """Layer 1 only runs once transcript size crosses MICROCOMPACT_THRESHOLD."""

    def test_no_op_at_or_below_threshold(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        for i in range(KEEP_RECENT + 5):
            messages.append(
                {"role": "tool", "content": f"{'x' * 200} result_{i}", "tool_call_id": f"tc_{i}"}
            )

        assert estimate_tokens(messages) <= MICROCOMPACT_THRESHOLD

        originals = [m["content"] for m in messages]
        _apply_microcompact_gate(messages)
        assert [m["content"] for m in messages] == originals

    def test_prunes_above_threshold(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        messages.append({"role": "user", "content": "x" * (MICROCOMPACT_THRESHOLD * 4 + 1000)})
        for i in range(KEEP_RECENT + 5):
            messages.append(
                {"role": "tool", "content": f"{'y' * 200} result_{i}", "tool_call_id": f"tc_{i}"}
            )

        assert estimate_tokens(messages) > MICROCOMPACT_THRESHOLD

        _apply_microcompact_gate(messages)

        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        cleared = [m for m in tool_msgs if m["content"] == "[cleared]"]
        preserved = [m for m in tool_msgs if m["content"] != "[cleared]"]
        assert len(cleared) == 5
        assert len(preserved) == KEEP_RECENT


# ---------------------------------------------------------------------------
# _context_collapse
# ---------------------------------------------------------------------------


class TestContextCollapse:
    def test_collapses_long_content(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        # Add enough messages to exceed COLLAPSE_PRESERVE_RECENT
        for i in range(COLLAPSE_PRESERVE_RECENT + 5):
            messages.append({"role": "user", "content": f"{'z' * (COLLAPSE_TEXT_MIN + 500)} msg_{i}"})

        _context_collapse(messages)

        # Early messages should be collapsed
        assert "collapsed" in messages[1]["content"]
        # Recent messages should be intact
        assert "collapsed" not in messages[-1]["content"]

    def test_skips_short_content(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        for i in range(COLLAPSE_PRESERVE_RECENT + 3):
            messages.append({"role": "user", "content": f"short msg {i}"})
        originals = [m["content"] for m in messages]
        _context_collapse(messages)
        # Nothing should change because all content is short
        for orig, msg in zip(originals, messages):
            assert msg["content"] == orig

    def test_skips_cleared_content(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        for _ in range(COLLAPSE_PRESERVE_RECENT + 3):
            messages.append({"role": "tool", "content": "[cleared]"})
        _context_collapse(messages)
        # [cleared] should remain [cleared], not be collapsed
        for m in messages[1:]:
            assert m["content"] == "[cleared]"

    def test_no_op_when_too_few_messages(self) -> None:
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "x" * 5000},
        ]
        _context_collapse(messages)
        assert "collapsed" not in messages[1]["content"]

    def test_preserves_head_and_tail(self) -> None:
        messages = [{"role": "system", "content": "sys"}]
        for i in range(COLLAPSE_PRESERVE_RECENT + 3):
            messages.append({"role": "user", "content": f"HEAD_MARKER{'x' * COLLAPSE_TEXT_MIN}TAIL_MARKER msg_{i}"})

        _context_collapse(messages)

        collapsed_msg = messages[1]["content"]
        assert "HEAD_MARKER" in collapsed_msg
        assert "TAIL_MARKER" in collapsed_msg
        assert "collapsed" in collapsed_msg


# ---------------------------------------------------------------------------
# _fix_tool_pairs
# ---------------------------------------------------------------------------


class TestFixToolPairs:
    def test_removes_orphan_result(self) -> None:
        messages = [
            {"role": "assistant", "content": "thinking", "tool_calls": [
                {"id": "tc_1", "function": {"name": "bash"}},
            ]},
            {"role": "tool", "tool_call_id": "tc_1", "name": "bash", "content": "ok"},
            # Orphan: no matching tool_call
            {"role": "tool", "tool_call_id": "tc_orphan", "name": "ghost", "content": "orphan"},
        ]
        _fix_tool_pairs(messages)
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["tool_call_id"] == "tc_1"

    def test_inserts_stub_for_orphan_call(self) -> None:
        messages = [
            {"role": "assistant", "content": "thinking", "tool_calls": [
                {"id": "tc_1", "function": {"name": "bash"}},
                {"id": "tc_2", "function": {"name": "read_file"}},
            ]},
            # Only result for tc_1, tc_2 is missing
            {"role": "tool", "tool_call_id": "tc_1", "name": "bash", "content": "ok"},
        ]
        _fix_tool_pairs(messages)
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 2
        stub = [m for m in tool_msgs if m["tool_call_id"] == "tc_2"]
        assert len(stub) == 1
        assert "earlier context" in stub[0]["content"]

    def test_no_op_when_balanced(self) -> None:
        messages = [
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "tc_1", "function": {"name": "bash"}},
            ]},
            {"role": "tool", "tool_call_id": "tc_1", "name": "bash", "content": "ok"},
        ]
        before = len(messages)
        _fix_tool_pairs(messages)
        assert len(messages) == before

    def test_handles_empty_messages(self) -> None:
        messages = []
        _fix_tool_pairs(messages)
        assert messages == []

    def test_multiple_orphans(self) -> None:
        messages = [
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "tc_1", "function": {"name": "a"}},
                {"id": "tc_2", "function": {"name": "b"}},
                {"id": "tc_3", "function": {"name": "c"}},
            ]},
            # No results at all
        ]
        _fix_tool_pairs(messages)
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 3


# ---------------------------------------------------------------------------
# _is_tool_success
# ---------------------------------------------------------------------------


class TestIsToolSuccess:
    def test_success_plain_text(self) -> None:
        assert _is_tool_success("some output text") is True

    def test_success_json_ok(self) -> None:
        assert _is_tool_success('{"status": "ok", "data": 42}') is True

    def test_failure_json_error(self) -> None:
        assert _is_tool_success('{"status": "error", "error": "boom"}') is False

    def test_success_non_dict_json(self) -> None:
        assert _is_tool_success("[1, 2, 3]") is True

    def test_success_empty_string(self) -> None:
        assert _is_tool_success("") is True

    def test_success_invalid_json(self) -> None:
        assert _is_tool_success("{not json}") is True


# ---------------------------------------------------------------------------
# _normalize_tool_run_dir
# ---------------------------------------------------------------------------


class TestNormalizeToolRunDir:
    def test_injects_memory_run_dir_when_missing(self) -> None:
        args = {"path": "config.json"}
        out = _normalize_tool_run_dir(args, "/tmp/run_123")
        assert out["run_dir"] == "/tmp/run_123"

    def test_resolves_relative_dot_to_memory_run_dir(self) -> None:
        args = {"run_dir": "."}
        out = _normalize_tool_run_dir(args, "/tmp/run_123")
        assert out["run_dir"] == str(Path("/tmp/run_123").resolve())

    def test_resolves_relative_child_to_memory_run_dir(self) -> None:
        args = {"run_dir": "risk_parity_run"}
        out = _normalize_tool_run_dir(args, "/tmp/run_123")
        assert out["run_dir"] == str((Path("/tmp/run_123") / "risk_parity_run").resolve())

    def test_preserves_absolute_run_dir(self) -> None:
        # ``os.path.abspath`` produces a platform-correct absolute path: on
        # POSIX it stays ``/var/tmp/custom_run``; on Windows it becomes
        # ``C:\var\tmp\custom_run``. ``Path.is_absolute()`` only treats the
        # latter as absolute on Windows, so the bare Unix-style literal would
        # otherwise be classified as relative and resolved against
        # ``memory_run_dir`` — defeating the point of the test.
        absolute_run_dir = os.path.abspath("/var/tmp/custom_run")
        args = {"run_dir": absolute_run_dir}
        out = _normalize_tool_run_dir(args, "/tmp/run_123")
        assert out["run_dir"] == absolute_run_dir
