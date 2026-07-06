"""Tests for the `vibe-trading memory` CLI subcommands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import cli
from src.memory.persistent import PersistentMemory


def _seed(tmp_path: Path) -> PersistentMemory:
    """Populate a tmp memory dir with one entry per type."""
    pm = PersistentMemory(memory_dir=tmp_path)
    pm.add("user-style", "Prefer concise replies.", "user", description="user persona")
    pm.add("feedback-tests", "Never mock the database.", "feedback", description="testing rule")
    pm.add("project-q2", "Q2 focus is execution loop.", "project", description="Q2 priorities")
    pm.add("ref-runbook", "See runbook.md", "reference", description="ops runbook pointer")
    return pm


class TestPersistentMemoryFind:
    def test_exact_title_wins(self, tmp_path: Path) -> None:
        pm = _seed(tmp_path)
        entry = pm.find("project-q2")
        assert entry is not None
        assert entry.title == "project-q2"

    def test_stem_match_full_form(self, tmp_path: Path) -> None:
        # On-disk stem `project_project-q2` matches via `stem == needle` branch.
        pm = _seed(tmp_path)
        entry = pm.find("project_project-q2")
        assert entry is not None
        assert entry.title == "project-q2"

    def test_stem_match_slug_suffix(self, tmp_path: Path) -> None:
        # Title differs from slug so the title-match loop misses; the
        # `stem.endswith(f"_{needle}")` branch is the one under test.
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("My Custom Title", "body", "user", description="d")
        entry = pm.find("my_custom_title")
        assert entry is not None
        assert entry.title == "My Custom Title"

    def test_missing_returns_none(self, tmp_path: Path) -> None:
        pm = _seed(tmp_path)
        assert pm.find("nope") is None

    def test_blank_returns_none(self, tmp_path: Path) -> None:
        pm = _seed(tmp_path)
        assert pm.find("   ") is None


class TestCmdMemoryList:
    def test_empty_dir_returns_success(self, tmp_path: Path) -> None:
        assert cli.cmd_memory_list(memory_dir=tmp_path) == cli.EXIT_SUCCESS

    def test_lists_all_entries(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_list(memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "user-style" in out
        assert "feedback-tests" in out
        assert "project-q2" in out
        assert "ref-runbook" in out
        assert "4 entries" in out

    def test_type_filter(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_list("feedback", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "feedback-tests" in out
        assert "user-style" not in out
        assert "1 entry" in out

    def test_type_filter_with_no_matches(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        PersistentMemory(memory_dir=tmp_path).add("only-user", "x", "user")
        rc = cli.cmd_memory_list("feedback", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "No memory entries found type=feedback" in out


class TestCmdMemoryShow:
    def test_shows_full_body(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_show("user-style", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "user-style" in out
        assert "Prefer concise replies." in out

    def test_missing_returns_usage_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_show("ghost", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_USAGE_ERROR
        assert "Memory not found" in out

    def test_resolves_by_slug(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_show("project_project-q2", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "Q2 focus" in out

    def test_empty_body_renders_placeholder(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("blank-mem", "", "user", description="empty body")
        rc = cli.cmd_memory_show("blank-mem", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "(empty body)" in out

    def test_rich_markup_in_title_is_escaped(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # Title containing Rich-like syntax must not be interpreted as markup.
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("evil[red]title", "ok", "user", description="d")
        rc = cli.cmd_memory_show("evil[red]title", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "evil[red]title" in out

    def test_list_does_not_crash_on_bracketed_description(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Regression: descriptions that look like YAML list literals are parsed
        # as lists. Without storage-layer coercion, rich.markup.escape() crashed
        # with TypeError because it only accepts strings.
        entry_path = tmp_path / "user_yaml-leak.md"
        entry_path.write_text(
            "---\nname: yaml-leak\ndescription: [red]inject[/red]\ntype: user\n---\n\nbody\n",
            encoding="utf-8",
        )
        rc = cli.cmd_memory_list(memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "yaml-leak" in out


class TestCmdMemorySearch:
    def test_finds_match(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_search("execution", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "project-q2" in out

    def test_no_match(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_search("xyzznope", memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "No matches" in out

    def test_limit_respected(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        for i in range(10):
            pm.add(f"runbook-{i}", "ops runbook content", "reference", description="runbook")
        results_2 = pm.find_relevant("runbook", max_results=2)
        results_5 = pm.find_relevant("runbook", max_results=5)
        assert len(results_2) == 2
        assert len(results_5) == 5


class TestCmdMemoryForget:
    def test_removes_with_yes_flag(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_forget("user-style", yes=True, memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_SUCCESS
        assert "Forgot" in out
        # File removed from disk
        remaining = {e.title for e in PersistentMemory(memory_dir=tmp_path).list_entries()}
        assert "user-style" not in remaining
        assert "feedback-tests" in remaining

    def test_missing_returns_usage_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        rc = cli.cmd_memory_forget("ghost", yes=True, memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_USAGE_ERROR
        assert "Memory not found" in out

    def test_confirmation_declined_keeps_entry(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        with patch.object(cli.Confirm, "ask", return_value=False):
            rc = cli.cmd_memory_forget("project-q2", yes=False, memory_dir=tmp_path)
        out = capsys.readouterr().out
        # Declining is a successful cancellation, mirroring cmd_init's overwrite prompt.
        assert rc == cli.EXIT_SUCCESS
        assert "Aborted" in out
        remaining = {e.title for e in PersistentMemory(memory_dir=tmp_path).list_entries()}
        assert "project-q2" in remaining

    def test_eof_in_non_interactive_context(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        with patch.object(cli.Confirm, "ask", side_effect=EOFError):
            rc = cli.cmd_memory_forget("project-q2", yes=False, memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_USAGE_ERROR
        assert "--yes" in out

    def test_remove_failure_returns_run_failed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _seed(tmp_path)
        with patch.object(PersistentMemory, "remove_entry", return_value=False):
            rc = cli.cmd_memory_forget("project-q2", yes=True, memory_dir=tmp_path)
        out = capsys.readouterr().out
        assert rc == cli.EXIT_RUN_FAILED
        assert "Failed to remove" in out


class TestParserWiring:
    def test_memory_list_parses(self) -> None:
        parser = cli._build_parser()
        args = parser.parse_args(["memory", "list", "--type", "feedback"])
        assert args.command == "memory"
        assert args.memory_command == "list"
        assert args.memory_type == "feedback"

    def test_memory_show_parses(self) -> None:
        parser = cli._build_parser()
        args = parser.parse_args(["memory", "show", "user-style"])
        assert args.memory_command == "show"
        assert args.name == "user-style"

    def test_memory_search_parses(self) -> None:
        parser = cli._build_parser()
        args = parser.parse_args(["memory", "search", "bitcoin", "--limit", "3"])
        assert args.memory_command == "search"
        assert args.query == "bitcoin"
        assert args.memory_limit == 3

    def test_memory_forget_parses(self) -> None:
        parser = cli._build_parser()
        args = parser.parse_args(["memory", "forget", "user-style", "-y"])
        assert args.memory_command == "forget"
        assert args.name == "user-style"
        assert args.yes is True

    def test_memory_no_subcommand(self) -> None:
        parser = cli._build_parser()
        args = parser.parse_args(["memory"])
        assert args.command == "memory"
        assert args.memory_command is None

    def test_memory_invalid_type_rejected(self) -> None:
        parser = cli._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["memory", "list", "--type", "garbage"])
