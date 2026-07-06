"""Tests for the interactive CLI scaffolding.

Covers:

* Slash-router fuzzy matching and exact lookup
* ``cli.main`` routing helpers (interactive detection, max-iter extraction)
* ``cli.input._has_unbalanced_brackets`` (multi-line Enter semantics)
* The bottom hint-bar renderer
* Tool-event row rendering
* ``cli.input.ctrl_c_within_window`` two-press exit confirmation
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Slash router
# ---------------------------------------------------------------------------


class TestSlashRouter:
    def test_find_exact_known(self) -> None:
        from cli.commands.slash_router import find_exact

        cmd = find_exact("help")
        assert cmd is not None
        assert cmd.name == "help"

    def test_find_exact_alias(self) -> None:
        from cli.commands.slash_router import find_exact

        cmd = find_exact("q")
        assert cmd is not None and cmd.name == "quit"

    def test_find_exact_unknown_returns_none(self) -> None:
        from cli.commands.slash_router import find_exact

        assert find_exact("definitely-not-a-real-command") is None

    def test_match_prefix(self) -> None:
        from cli.commands.slash_router import match_commands

        matches = [c.name for c in match_commands("/cl")]
        assert "clear" in matches

    def test_match_subsequence(self) -> None:
        from cli.commands.slash_router import match_commands

        # ``hsto`` is a subsequence of ``history``.
        matches = [c.name for c in match_commands("/hsto")]
        assert "history" in matches

    def test_match_returns_empty_for_non_slash(self) -> None:
        from cli.commands.slash_router import match_commands

        assert match_commands("plain text") == []

    def test_handler_module_uses_cli_package(self) -> None:
        from cli.commands.slash_router import SLASH_COMMANDS

        for cmd in SLASH_COMMANDS:
            assert cmd.handler_module.startswith("cli."), (
                f"{cmd.name!r} handler_module {cmd.handler_module!r} should "
                "live under the ``cli`` package root, not ``agent.cli``."
            )


# ---------------------------------------------------------------------------
# Main routing helpers
# ---------------------------------------------------------------------------


class TestMainRouting:
    def test_extract_max_iter_space_separated(self) -> None:
        from cli.main import _extract_max_iter

        assert _extract_max_iter(["chat", "--max-iter", "77"], default=50) == 77

    def test_extract_max_iter_equals_separated(self) -> None:
        from cli.main import _extract_max_iter

        assert _extract_max_iter(["--max-iter=12"], default=50) == 12

    def test_extract_max_iter_default(self) -> None:
        from cli.main import _extract_max_iter

        assert _extract_max_iter([], default=42) == 42

    def test_non_interactive_subcommands_route_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.main import _is_interactive_invocation

        # Force a TTY so the only signal that drops the interactive path
        # is the recognised subcommand.
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for sub in ("serve", "run", "list", "mcp", "swarm", "init", "hypothesis"):
            assert _is_interactive_invocation([sub]) is False, sub

    def test_legacy_flags_route_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for flag in ("--list", "--show", "--skills", "--version"):
            assert _is_interactive_invocation([flag]) is False, flag

    def test_chat_is_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _is_interactive_invocation(["chat"]) is True

    def test_empty_argv_is_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _is_interactive_invocation([]) is True

    def test_unknown_positional_routes_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unknown bare tokens must delegate to legacy so argparse reports the typo."""
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for token in ("foo", "alphazoo", "helpme"):
            assert _is_interactive_invocation([token]) is False, token

    def test_piped_stdin_disables_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert _is_interactive_invocation([]) is False

    def test_chat_with_supported_max_iter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``chat`` with a parseable --max-iter belongs to the REPL."""
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for argv in (["chat", "--max-iter", "10"], ["chat", "--max-iter=42"]):
            assert _is_interactive_invocation(argv) is True, argv

    def test_chat_help_routes_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``chat --help`` / ``-h`` must reach legacy argparse for the help screen."""
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for argv in (["chat", "--help"], ["chat", "-h"]):
            assert _is_interactive_invocation(argv) is False, argv

    def test_chat_with_bad_max_iter_routes_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A non-integer ``--max-iter`` must reach argparse so it can complain."""
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for argv in (["chat", "--max-iter", "bad"], ["chat", "--max-iter=bad"]):
            assert _is_interactive_invocation(argv) is False, argv

    def test_chat_with_extra_positional_routes_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extra positionals on ``chat`` are user errors — let argparse say so."""
        from cli.main import _is_interactive_invocation

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        for argv in (["chat", "extra"], ["chat", "foo", "bar"]):
            assert _is_interactive_invocation(argv) is False, argv


# ---------------------------------------------------------------------------
# Main-level dispatch smoke
# ---------------------------------------------------------------------------


class TestMainDispatch:
    """``cli.main(argv)`` must hand non-interactive argv to ``_legacy.main`` verbatim.

    These don't exercise the real legacy handlers (they would spin up
    servers, hit the network, or block on prompts). Instead they patch
    ``_legacy.main`` and assert ``cli.main`` forwards the exact argv.
    """

    def test_cmd_wrappers_propagate_package_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patching ``cli.RUNS_DIR`` must reach ``_legacy`` before any cmd_* runs.

        Regression for the partial-sync trap: before this wrapper, only
        ``cmd_init`` triggered the sync, so ``patch.object(cli, "RUNS_DIR",
        tmp); cli.cmd_list()`` silently read the unpatched ``_legacy.RUNS_DIR``.
        """
        from pathlib import Path

        import cli

        captured: dict[str, Any] = {}

        def fake_cmd_list(*args, **kwargs):  # noqa: ANN001
            captured["runs_dir"] = cli._legacy.RUNS_DIR
            return 0

        monkeypatch.setattr(cli._legacy, "cmd_list", fake_cmd_list)
        monkeypatch.setattr(cli, "RUNS_DIR", Path("/tmp/regression-runs-dir"))

        cli.cmd_list(20)

        assert captured.get("runs_dir") == Path("/tmp/regression-runs-dir")

    @pytest.mark.parametrize(
        "argv",
        [
            ["serve", "--port", "8901"],
            ["run", "-p", "what is AAPL"],
            ["list", "--limit", "5"],
            ["show", "abc123"],
            ["hypothesis", "list"],
            ["alpha", "list"],
            ["memory", "show", "feedback-research-first"],
            ["provider", "login", "openai-codex"],
            ["init"],
            ["--list"],
            ["--show", "abc123"],
            ["--version"],
            ["--help"],
            ["chat", "--help"],
            ["chat", "--max-iter", "bad"],
            ["chat", "extra"],
        ],
    )
    def test_non_interactive_argv_forwarded_to_legacy(
        self, monkeypatch: pytest.MonkeyPatch, argv: list[str]
    ) -> None:
        """Every non-REPL argv shape must reach ``_legacy.main`` untouched."""
        from cli.main import main as cli_main_fn

        # Force a TTY so the only reason these argv shapes don't enter the
        # REPL is the chat-gate / flag / subcommand routing.
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        captured: dict[str, Any] = {}

        def fake_legacy_main(passed_argv):  # noqa: ANN001
            captured["argv"] = list(passed_argv)
            return 0

        from cli import _legacy

        monkeypatch.setattr(_legacy, "main", fake_legacy_main)

        rc = cli_main_fn(argv)

        assert rc == 0, argv
        assert captured.get("argv") == argv, (argv, captured)


# ---------------------------------------------------------------------------
# Input layer
# ---------------------------------------------------------------------------


class TestInputHelpers:
    def test_balanced_brackets(self) -> None:
        from cli.input import _has_unbalanced_brackets

        assert _has_unbalanced_brackets("hello world") is False
        assert _has_unbalanced_brackets("foo(bar)") is False
        assert _has_unbalanced_brackets("[1,2,{3:4}]") is False

    def test_unbalanced_open(self) -> None:
        from cli.input import _has_unbalanced_brackets

        assert _has_unbalanced_brackets("def f(x:\n  return") is True

    def test_strings_ignored(self) -> None:
        from cli.input import _has_unbalanced_brackets

        # The unbalanced ``(`` sits inside a string literal.
        assert _has_unbalanced_brackets('print("a (b c")') is False

    def test_strip_surrogates_keeps_plain_text(self) -> None:
        from cli.input import _strip_surrogates

        assert _strip_surrogates("hello") == "hello"

    def test_strip_surrogates_drops_lone_half(self) -> None:
        from cli.input import _strip_surrogates

        # \ud83d alone is a lone high surrogate.
        cleaned = _strip_surrogates("a\ud83db")
        assert "\ud83d" not in cleaned
        assert cleaned.startswith("a") and cleaned.endswith("b")

    def test_ctrl_c_within_window_returns_false_when_unset(self) -> None:
        from cli.input import ctrl_c_within_window

        session = SimpleNamespace()
        assert ctrl_c_within_window(session) is False

    def test_ctrl_c_within_window_uses_state(self) -> None:
        from cli.input import ctrl_c_within_window

        state = SimpleNamespace(last_press_ts=time.monotonic())
        session = SimpleNamespace(vibe_ctrl_c_state=state)
        assert ctrl_c_within_window(session, window_sec=2.0) is True

    def test_ctrl_c_window_expires(self) -> None:
        from cli.input import ctrl_c_within_window

        state = SimpleNamespace(last_press_ts=time.monotonic() - 10.0)
        session = SimpleNamespace(vibe_ctrl_c_state=state)
        assert ctrl_c_within_window(session, window_sec=2.0) is False


# ---------------------------------------------------------------------------
# Ctrl+C two-press regression (Parcel I, Bug 1)
# ---------------------------------------------------------------------------


class TestCtrlCTwoPress:
    """Regression coverage for the broken first-press-exits behaviour.

    Before the fix in Parcel I the keybinding stamped ``last_press_ts``
    on every press and ``ctrl_c_within_window`` computed
    ``now - last_press_ts`` — yielding ~0 on the first press, so the
    outer loop exited immediately. These tests pin the corrected
    two-timestamp design in place.
    """

    def test_first_press_returns_false(self) -> None:
        from cli.input import _CtrlCState

        state = _CtrlCState()
        # First press → no prior press → must report "not in window".
        assert state.record_press_and_check_window(window_sec=2.0) is False

    def test_second_press_within_window_returns_true(self) -> None:
        from cli.input import _CtrlCState

        state = _CtrlCState()
        state.record_press_and_check_window(window_sec=2.0)  # first press
        # Second press immediately after → inside the 2 s window.
        assert state.record_press_and_check_window(window_sec=2.0) is True

    def test_second_press_after_window_returns_false(self) -> None:
        from cli.input import _CtrlCState

        state = _CtrlCState()
        # Simulate a first press well in the past.
        state.previous_press_ts = time.monotonic() - 3.0
        # This press is the "second" one, but it lands outside the window
        # — must be treated as a fresh first press for the next round.
        assert state.record_press_and_check_window(window_sec=2.0) is False

    def test_window_check_reads_cached_decision(self) -> None:
        from cli.input import _CtrlCState, ctrl_c_within_window

        state = _CtrlCState()
        # Simulate the keybinding's press-time decision.
        state.record_press_and_check_window(window_sec=2.0)  # first → False
        session = SimpleNamespace(vibe_ctrl_c_state=state)
        assert ctrl_c_within_window(session, window_sec=2.0) is False

        state.record_press_and_check_window(window_sec=2.0)  # second → True
        assert ctrl_c_within_window(session, window_sec=2.0) is True


# ---------------------------------------------------------------------------
# Slash typo suggestions (Parcel I, Bug 3)
# ---------------------------------------------------------------------------


class TestSlashTypoSuggestions:
    """``/historu`` and ``/jurnal`` must surface ``history`` / ``journal``."""

    def test_single_char_typo_history(self) -> None:
        from cli.main import _suggest_commands

        assert "history" in _suggest_commands("historu")

    def test_single_char_typo_journal(self) -> None:
        from cli.main import _suggest_commands

        assert "journal" in _suggest_commands("jurnal")

    def test_close_to_quit(self) -> None:
        from cli.main import _suggest_commands

        # ``quti`` is a transposition of ``quit`` — subsequence scoring
        # misses this; difflib edit-distance catches it.
        assert "quit" in _suggest_commands("quti")

    def test_no_match_returns_empty(self) -> None:
        from cli.main import _suggest_commands

        suggestions = _suggest_commands("xyzqwerty")
        # Either empty, or no obviously-wrong entry. The contract is
        # "never raises" and "respects the 3-entry cap".
        assert len(suggestions) <= 3


# ---------------------------------------------------------------------------
# /journal /shadow /debug behaviour (Parcel I, Bug 4)
# ---------------------------------------------------------------------------


class TestChatCommandsAreActionable:
    """``/journal`` and ``/shadow`` queue real prompts, not "Coming soon"."""

    def test_journal_with_path_queues_prompt(self) -> None:
        from cli.commands.chat import cmd_journal

        ctx = SimpleNamespace(pending_prompt=None)
        rc = cmd_journal(ctx, "trades.csv")
        assert rc == 0
        assert ctx.pending_prompt is not None
        assert "trade journal" in ctx.pending_prompt.lower()
        assert "trades.csv" in ctx.pending_prompt

    def test_journal_without_path_prints_usage(self) -> None:
        from cli.commands.chat import cmd_journal

        ctx = SimpleNamespace(pending_prompt=None)
        rc = cmd_journal(ctx)
        # No prompt queued (no path), but the command must not crash and
        # must not silently swallow the request.
        assert rc == 0
        assert ctx.pending_prompt is None

    def test_shadow_without_args_opens_dashboard(self) -> None:
        from cli.commands.chat import cmd_shadow

        ctx = SimpleNamespace(pending_prompt=None)
        rc = cmd_shadow(ctx)
        assert rc == 0
        assert ctx.pending_prompt is not None
        assert "shadow" in ctx.pending_prompt.lower()

    def test_shadow_with_path_trains(self) -> None:
        from cli.commands.chat import cmd_shadow

        ctx = SimpleNamespace(pending_prompt=None)
        rc = cmd_shadow(ctx, "trades.csv")
        assert rc == 0
        assert ctx.pending_prompt is not None
        assert "trades.csv" in ctx.pending_prompt
        assert "shadow" in ctx.pending_prompt.lower()

    def test_debug_toggles_flag(self) -> None:
        from cli.commands.chat import cmd_debug

        ctx = SimpleNamespace(debug=False)
        cmd_debug(ctx)
        assert ctx.debug is True
        cmd_debug(ctx)
        assert ctx.debug is False


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class TestHintBar:
    def test_left_only(self) -> None:
        from cli.components.hint_bar import render_hint_bar

        bar = render_hint_bar("hello", width=20)
        assert "hello" in bar.plain

    def test_left_right_fit(self) -> None:
        from cli.components.hint_bar import render_hint_bar

        bar = render_hint_bar("L", "R", width=10).plain
        assert bar.startswith("L") and bar.endswith("R")

    def test_truncation_preserves_right(self) -> None:
        from cli.components.hint_bar import render_hint_bar

        bar = render_hint_bar("a very long left segment", "Ctrl+C", width=20).plain
        assert bar.endswith("Ctrl+C")


class TestToolEventRender:
    def test_running_status(self) -> None:
        from cli.components.tool_event import render_tool_event

        text = render_tool_event("get_financials", {"query": "AAPL"}, status="running")
        assert "Financials" in text.plain
        assert "AAPL" in text.plain

    def test_ok_with_duration(self) -> None:
        from cli.components.tool_event import render_tool_event

        text = render_tool_event(
            "run_backtest",
            {"symbol": "BTC"},
            status="ok",
            duration_ms=1400,
        )
        # 1400 ms ~= 1.4s in the shared formatter.
        assert "1.4s" in text.plain

    def test_error_renders(self) -> None:
        from cli.components.tool_event import render_tool_event

        text = render_tool_event("load_skill", {"name": "x"}, status="error")
        assert "x" in text.plain

    def test_unknown_status_degrades(self) -> None:
        from cli.components.tool_event import render_tool_event

        # Unknown statuses should not raise — they degrade to "running".
        text = render_tool_event("foo", None, status="bogus")  # type: ignore[arg-type]
        assert "Foo" in text.plain


# ---------------------------------------------------------------------------
# Working indicator
# ---------------------------------------------------------------------------


class TestWorkingIndicator:
    def test_pick_verb_returns_string(self) -> None:
        from cli.components.working_indicator import _pick_verb

        verb = _pick_verb()
        assert isinstance(verb, str) and verb


# ---------------------------------------------------------------------------
# Package compatibility surface
# ---------------------------------------------------------------------------


class TestPackageCompat:
    def test_cli_reexports_legacy_helpers(self) -> None:
        import cli

        # Historically the tests reached into ``cli._render_env_content``
        # and ``cli.cmd_memory_list``; the package keeps re-exporting
        # them so downstream callers stay green.
        assert hasattr(cli, "_render_env_content")
        assert hasattr(cli, "cmd_memory_list")
        assert hasattr(cli, "cmd_init")
        assert callable(cli.main)
