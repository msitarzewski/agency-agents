"""Tests for swarm worker report.md → summary handoff."""

from __future__ import annotations

from pathlib import Path

from src.swarm.worker import _preview_tool_arguments, _resolve_summary, _best_summary


def test_resolve_summary_reads_report_md(tmp_path: Path) -> None:
    """When report.md exists in artifact dir, _resolve_summary returns its content."""
    report_content = "# Analysis Report\n\nKey finding: bullish."
    (tmp_path / "report.md").write_text(report_content, encoding="utf-8")

    result = _resolve_summary(tmp_path, "short fallback")
    assert result == report_content


def test_resolve_summary_falls_back_when_no_report(tmp_path: Path) -> None:
    """When report.md does not exist, _resolve_summary returns the fallback."""
    result = _resolve_summary(tmp_path, "short fallback")
    assert result == "short fallback"


def test_resolve_summary_falls_back_when_empty_report(tmp_path: Path) -> None:
    """When report.md is empty/whitespace, _resolve_summary returns the fallback."""
    (tmp_path / "report.md").write_text("   \n\n  ", encoding="utf-8")

    result = _resolve_summary(tmp_path, "short fallback")
    assert result == "short fallback"


def test_best_summary_picks_longest_assistant_text() -> None:
    """_best_summary returns the longest assistant message over 100 chars."""
    messages = [
        {"role": "assistant", "content": "Short text"},
        {"role": "assistant", "content": "A" * 200},
        {"role": "assistant", "content": "B" * 300},
    ]
    result = _best_summary(messages, "fallback")
    assert result == "B" * 300


def test_best_summary_falls_back() -> None:
    """_best_summary returns fallback when no assistant messages qualify."""
    messages = [{"role": "user", "content": "hello"}]
    result = _best_summary(messages, "fallback")
    assert result == "fallback"


def test_resolve_summary_handles_read_error(tmp_path: Path) -> None:
    """_resolve_summary returns fallback if reading report.md fails."""
    result = _resolve_summary(Path("/nonexistent/path/xyz"), "fallback")
    assert result == "fallback"


def test_preview_tool_arguments_redacts_sensitive_values() -> None:
    """Event previews should not leak file bodies or credentials."""
    preview = _preview_tool_arguments({
        "path": "report.md",
        "content": "# very long confidential report",
        "headers": {"Authorization": "Bearer secret-token"},
        "api_token": "secret-token",
        "run_dir": "/tmp/hidden",
    })

    assert preview == {
        "path": "report.md",
        "content": "[redacted]",
        "headers": "[redacted]",
        "api_token": "[redacted]",
    }


def test_preview_tool_arguments_truncates_non_sensitive_values() -> None:
    """Non-sensitive event previews stay short."""
    preview = _preview_tool_arguments({"query": "A" * 250})
    assert preview["query"] == "A" * 200 + "..."
