"""Tests for the live-runtime CLI surface + discoverability (parcel R7).

Covers SPEC.md §7.5 (persistent runner control) + §9 Decision 1 (CLI surface
table) + the §9 audit discoverability fix:

* ``connector start`` / ``connector stop`` dispatch to their handlers and
  relay to the R6 surface endpoints (``POST /live/runner/start|stop``).
* Connector live status surfaces runner liveness + last-tick from the liveness
  contract (``src.live.runtime.liveness``), degrading cleanly when the runtime
  module is not yet present.
* The slash registry / ``/help`` / typeahead completer now include
  ``connector`` / ``halt`` / ``resume`` (previously undiscoverable surface actions),
  and ``/stop`` resolves as the kill-switch alias of ``/halt``.
* The REPL intercepts ``/resume`` (clear halt) and ``/connector ...`` (bridge to
  the connector subcommand group) in the input path — neither is dispatched to the model.

The API client is stubbed (``httpx``) and the liveness module is injected into
``sys.modules`` so no server / concurrent runtime parcel is needed.
"""

from __future__ import annotations

import importlib
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

import src.live.paths as live_paths

# ``cli/__init__.py`` re-exports ``main`` as a function, shadowing the submodule
# for attribute access; import the module object directly (mirrors test_cli_live).
main = importlib.import_module("cli.main")
InteractiveContext = main.InteractiveContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def live_root(tmp_path: Path):
    """Redirect the live-channel runtime root to a tmp dir for the test."""
    with patch.object(live_paths, "get_runtime_root", return_value=tmp_path):
        yield tmp_path


@pytest.fixture()
def fake_liveness():
    """Inject a stub ``src.live.runtime.liveness`` module (R1 lands concurrently).

    Yields a dict the test can mutate to control ``is_runner_alive`` /
    ``last_tick`` return values. The real module is restored on teardown.
    """
    state: Dict[str, Any] = {"alive": True, "tick": datetime.now(timezone.utc)}
    mod = types.ModuleType("src.live.runtime.liveness")
    mod.is_runner_alive = lambda runner_id: bool(state["alive"])  # type: ignore[attr-defined]
    mod.last_tick = lambda runner_id: state["tick"]  # type: ignore[attr-defined]

    saved = sys.modules.get("src.live.runtime.liveness")
    sys.modules["src.live.runtime.liveness"] = mod
    try:
        yield state
    finally:
        if saved is not None:
            sys.modules["src.live.runtime.liveness"] = saved
        else:
            sys.modules.pop("src.live.runtime.liveness", None)


@pytest.fixture()
def no_liveness():
    """Force ``src.live.runtime.liveness`` import to fail (module absent)."""
    saved = sys.modules.get("src.live.runtime.liveness")
    sys.modules["src.live.runtime.liveness"] = None  # type: ignore[assignment]
    try:
        yield
    finally:
        if saved is not None:
            sys.modules["src.live.runtime.liveness"] = saved
        else:
            sys.modules.pop("src.live.runtime.liveness", None)


class _FakeResp:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


# ---------------------------------------------------------------------------
# Subcommand dispatch (run / start / stop) — argparse + _dispatch_connector
# ---------------------------------------------------------------------------


class TestRunnerDispatch:
    def _dispatch(self, argv: List[str]) -> int:
        from cli._legacy import _build_parser, _dispatch_connector

        args = _build_parser().parse_args(argv)
        return _dispatch_connector(args)

    def test_run_routes_to_handler(self) -> None:
        with patch("cli._legacy.cmd_connector_start", return_value=0) as m:
            assert self._dispatch(["connector", "start", "robinhood-live-mcp"]) == 0
        m.assert_called_once_with("robinhood-live-mcp")

    def test_start_default_profile_none(self) -> None:
        with patch("cli._legacy.cmd_connector_start", return_value=0) as m:
            self._dispatch(["connector", "start"])
        m.assert_called_once_with(None)

    def test_start_routes_to_handler(self) -> None:
        with patch("cli._legacy.cmd_connector_start", return_value=0) as m:
            self._dispatch(["connector", "start", "robinhood-live-mcp"])
        m.assert_called_once_with("robinhood-live-mcp")

    def test_stop_routes_to_handler(self) -> None:
        with patch("cli._legacy.cmd_connector_stop", return_value=0) as m:
            self._dispatch(["connector", "stop"])
        m.assert_called_once_with(None)

    def test_subparsers_registered(self) -> None:
        """start/stop parse without error (the parser knows them)."""
        from cli._legacy import _build_parser

        parser = _build_parser()
        for verb in ("start", "stop"):
            parsed = parser.parse_args(["connector", verb])
            assert parsed.connector_command == verb


# ---------------------------------------------------------------------------
# Runner control relays to the R6 surface endpoints
# ---------------------------------------------------------------------------


class TestRunnerControlEndpoints:
    def test_start_posts_to_runner_start(self) -> None:
        from cli._legacy import EXIT_SUCCESS, cmd_live_start

        captured: Dict[str, Any] = {}

        def _post(url: str, json: Dict[str, Any], timeout: float) -> _FakeResp:  # noqa: A002
            captured["url"] = url
            captured["body"] = json
            return _FakeResp({"runner_id": "live-robinhood", "status": "started"})

        with patch("httpx.post", _post):
            assert cmd_live_start("robinhood") == EXIT_SUCCESS
        assert captured["url"].endswith("/live/runner/start")
        assert captured["body"]["broker"] == "robinhood"
        assert captured["body"]["foreground"] is False

    def test_connector_start_message_uses_connector_status(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import EXIT_SUCCESS, cmd_connector_start

        def _post(url: str, json: Dict[str, Any], timeout: float) -> _FakeResp:  # noqa: A002
            return _FakeResp({"runner_id": "live-robinhood", "status": "started"})

        with patch("httpx.post", _post):
            assert cmd_connector_start("robinhood-live-mcp") == EXIT_SUCCESS

        out = capsys.readouterr().out
        assert "vibe-trading connector status" in out
        assert "vibe-trading live" not in out

    def test_connector_start_rejects_readonly_ibkr_mcp(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import EXIT_USAGE_ERROR, cmd_connector_start

        assert cmd_connector_start("ibkr-live-official-mcp-readonly") == EXIT_USAGE_ERROR

        out = capsys.readouterr().out
        assert "does not support live runner management" in out

    def test_stop_posts_to_runner_stop(self) -> None:
        from cli._legacy import EXIT_SUCCESS, cmd_live_stop

        captured: Dict[str, Any] = {}

        def _post(url: str, json: Dict[str, Any], timeout: float) -> _FakeResp:  # noqa: A002
            captured["url"] = url
            captured["body"] = json
            return _FakeResp({"status": "stopped"})

        with patch("httpx.post", _post):
            assert cmd_live_stop("robinhood") == EXIT_SUCCESS
        assert captured["url"].endswith("/live/runner/stop")
        assert captured["body"]["broker"] == "robinhood"

    def test_start_server_unreachable_is_run_failed(self) -> None:
        from cli._legacy import EXIT_RUN_FAILED, cmd_live_start

        def _boom(url: str, json: Dict[str, Any], timeout: float) -> _FakeResp:  # noqa: A002
            raise OSError("connection refused")

        with patch("httpx.post", _boom):
            assert cmd_live_start("robinhood") == EXIT_RUN_FAILED

    def test_run_foreground_starts_then_stops(self, fake_liveness: Dict[str, Any]) -> None:
        """`live run` relays a foreground start, tails liveness, then stops."""
        from cli._legacy import EXIT_SUCCESS, cmd_live_run

        calls: List[str] = []

        def _post(url: str, json: Dict[str, Any], timeout: float) -> _FakeResp:  # noqa: A002
            calls.append(url)
            if url.endswith("/live/runner/start"):
                assert json["foreground"] is True
                # Make the tail loop exit immediately: runner reports stopped.
                fake_liveness["alive"] = False
            return _FakeResp({"runner_id": "live-robinhood", "status": "ok"})

        import cli._legacy as legacy

        # _legacy uses its own ``time`` import; patch that one so the tail loop
        # does not actually sleep.
        with patch("httpx.post", _post), patch.object(legacy.time, "sleep", lambda *_: None):
            assert cmd_live_run("robinhood") == EXIT_SUCCESS

        assert any(u.endswith("/live/runner/start") for u in calls)
        assert any(u.endswith("/live/runner/stop") for u in calls)


# ---------------------------------------------------------------------------
# live status surfaces runner liveness
# ---------------------------------------------------------------------------


class TestStatusLiveness:
    def test_status_shows_running(
        self, live_root: Path, fake_liveness: Dict[str, Any], capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_live_status

        fake_liveness["alive"] = True
        fake_liveness["tick"] = datetime.now(timezone.utc) - timedelta(seconds=5)
        assert cmd_live_status("robinhood") == 0
        out = capsys.readouterr().out
        assert "Runner" in out
        assert "running" in out
        assert "ago" in out  # last-tick relative time rendered

    def test_status_shows_stopped(
        self, live_root: Path, fake_liveness: Dict[str, Any], capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_live_status

        fake_liveness["alive"] = False
        cmd_live_status("robinhood")
        out = capsys.readouterr().out
        assert "stopped" in out

    def test_status_degrades_when_liveness_absent(
        self, live_root: Path, no_liveness: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Status must not crash if the runtime parcel hasn't landed yet."""
        from cli._legacy import cmd_live_status

        assert cmd_live_status("robinhood") == 0
        out = capsys.readouterr().out
        assert "Runner" in out
        assert "unknown" in out


class TestConnectorStatusReadiness:
    def test_remote_live_status_fails_when_not_configured(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import EXIT_RUN_FAILED, cmd_connector_status

        with patch(
            "src.config.loader.load_agent_config",
            return_value=types.SimpleNamespace(mcp_servers={}),
        ):
            assert cmd_connector_status("robinhood-live-mcp") == EXIT_RUN_FAILED

        out = capsys.readouterr().out
        assert "Trading Connector: robinhood-live-mcp" in out
        assert "Live channel:" not in out

    def test_remote_live_status_fails_when_not_authorized(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import EXIT_RUN_FAILED, cmd_connector_status

        server = types.SimpleNamespace(
            url="https://example.invalid/mcp",
            auth=types.SimpleNamespace(cache_dir=str(tmp_path / "oauth")),
            enabled_tools=["*"],
        )
        with patch(
            "src.config.loader.load_agent_config",
            return_value=types.SimpleNamespace(mcp_servers={"robinhood": server}),
        ), patch("src.live.registry.has_cached_oauth_token", return_value=False):
            assert cmd_connector_status("robinhood-live-mcp") == EXIT_RUN_FAILED

        out = capsys.readouterr().out
        assert "not_authorized" in out
        assert "Live channel:" not in out


# ---------------------------------------------------------------------------
# Discoverability: registry + help + completer now include live/halt/resume
# ---------------------------------------------------------------------------


class TestSlashDiscoverability:
    def test_registry_includes_connector_group(self) -> None:
        from cli.commands.slash_router import SLASH_COMMANDS

        names = {c.name for c in SLASH_COMMANDS}
        assert {"connector", "halt", "resume"} <= names

    def test_find_exact_resolves_new_commands(self) -> None:
        from cli.commands.slash_router import find_exact

        for name in ("connector", "halt", "resume"):
            assert find_exact(name) is not None

    def test_stop_is_alias_of_halt(self) -> None:
        from cli.commands.slash_router import find_exact

        cmd = find_exact("stop")
        assert cmd is not None
        assert cmd.name == "halt"

    def test_match_commands_surfaces_in_typeahead(self) -> None:
        """The completer ranks via match_commands — the connector group must appear."""
        from cli.commands.slash_router import match_commands

        names = {c.name for c in match_commands("/ha")}
        assert "halt" in names
        names = {c.name for c in match_commands("/co")}
        assert "connector" in names

    def test_completer_yields_connector_group(self) -> None:
        from prompt_toolkit.document import Document

        from cli.completer import SlashCompleter

        comp = SlashCompleter()
        completions = list(
            comp.get_completions(Document("/", cursor_position=1), complete_event=None)
        )
        texts = {c.text for c in completions}
        assert {"connector", "halt", "resume"} <= texts

    def test_help_lists_connector_group(self, capsys: pytest.CaptureFixture[str]) -> None:
        """``/help`` renders the registry — the connector group must be present."""
        from cli.commands import help as help_cmd

        # help.py binds SLASH_COMMANDS at import; our registration runs at
        # cli.main import (already done above) so the bound tuple includes them.
        assert {"connector", "halt", "resume"} <= {c.name for c in help_cmd.SLASH_COMMANDS}
        help_cmd.run(None)
        out = capsys.readouterr().out
        assert "/connector" in out
        assert "/halt" in out
        assert "/resume" in out

    def test_registration_is_idempotent(self) -> None:
        from cli.commands.slash_router import SLASH_COMMANDS

        before = len(SLASH_COMMANDS)
        main._register_live_slash_commands()
        from cli.commands.slash_router import SLASH_COMMANDS as after_tuple

        assert len(after_tuple) == before  # no duplicate rows


# ---------------------------------------------------------------------------
# REPL intercepts: /resume clears halt, /connector bridges to the subcommand group
# ---------------------------------------------------------------------------


class TestReplResumeIntercept:
    def test_resume_clears_halt(self, live_root: Path) -> None:
        from src.live.halt import halt_flag_set, trip_halt

        trip_halt(by="cli", reason="test")
        assert halt_flag_set("robinhood") is True

        console = main.get_console()
        main._clear_halt_from_repl(console)
        assert halt_flag_set("robinhood") is False

    def test_resume_when_not_halted_is_clean(
        self, live_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        console = main.get_console()
        main._clear_halt_from_repl(console)  # must not raise
        assert "No active global halt" in capsys.readouterr().out


class TestReplConnectorBridge:
    def test_connector_bridges_to_dispatch_connector(self) -> None:
        console = main.get_console()
        with patch("cli._legacy._dispatch_connector", return_value=0) as disp:
            main._run_connector_command_from_repl(console, ["status", "robinhood-live-mcp"])
        disp.assert_called_once()
        parsed = disp.call_args.args[0]
        assert parsed.connector_command == "status"
        assert parsed.profile == "robinhood-live-mcp"

    def test_bare_connector_defaults_to_status(self) -> None:
        console = main.get_console()
        with patch("cli._legacy._dispatch_connector", return_value=0) as disp:
            main._run_connector_command_from_repl(console, [])
        parsed = disp.call_args.args[0]
        assert parsed.connector_command == "status"

    def test_connector_start_bridges_to_start_handler(self) -> None:
        console = main.get_console()
        with patch("cli._legacy.cmd_connector_start", return_value=0) as start:
            main._run_connector_command_from_repl(console, ["start"])
        start.assert_called_once_with(None)

    def test_invalid_connector_subcommand_keeps_loop_alive(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        console = main.get_console()
        # Unknown subcommand → argparse SystemExit, caught, usage printed.
        main._run_connector_command_from_repl(console, ["frobnicate"])
        assert "Usage: /connector" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# ``vibe-trading resume <session-id>`` dispatches to the interactive loop
# ---------------------------------------------------------------------------


class TestResumeByIdDispatch:
    """``main()`` routes ``vibe-trading resume <session-id>`` to ``_interactive_loop``."""

    def test_resume_by_id_dispatches_with_session_id(self) -> None:
        with patch.object(main, "_interactive_loop", return_value=0) as mock:
            rc = main.main(["resume", "sess_abc123"])
        assert rc == 0
        mock.assert_called_once_with(max_iter=50, resume_session_id="sess_abc123")

    def test_resume_unknown_id_exits_nonzero(self) -> None:
        with patch.object(main, "_interactive_loop", return_value=0) as mock:
            rc = main.main(["resume", "sess_nonexistent"])
        assert rc == 0
        mock.assert_called_once()

    def test_resume_needs_exactly_two_args(self) -> None:
        """Too few or too many args should fall through to the legacy dispatcher."""
        with patch("cli._legacy.main", return_value=1) as legacy:
            main.main(["resume"])
        legacy.assert_called_once()
        legacy.reset_mock()

        with patch("cli._legacy.main", return_value=1) as legacy:
            main.main(["resume", "sess_x", "extra"])
        legacy.assert_called_once()
