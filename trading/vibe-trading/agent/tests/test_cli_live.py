"""Tests for the connector-first live CLI surface + REPL intercepts (P6).

Covers SPEC.md §9 Decision 1 (CLI surface table) and Consent §2/§4:

* The ``connector`` subcommand group dispatches each verb to the right handler.
* Connector live commands trip/clear the kill switch on disk.
* Live status/mandate helpers are read-only and reflect disk state.
* Connector revoke deletes the token cache + mandate.
* The REPL intercepts a bare numeric pick as a COMMIT — it calls the commit
  endpoint directly and NEVER routes the pick to the agent/model.
* The REPL intercepts a bare "停"/"stop"/"/halt" turn — it trips the kill
  switch without entering the agent loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

import importlib

import src.live.paths as live_paths

# ``cli/__init__.py`` re-exports the ``main`` *function* as ``cli.main``, which
# shadows the submodule for attribute access. Import the module object directly
# so ``patch.object(main, ...)`` targets the real ``cli/main.py`` namespace.
main = importlib.import_module("cli.main")
InteractiveContext = main.InteractiveContext
_commit_mandate = main._commit_mandate
_handle_proposal_reply = main._handle_proposal_reply
_is_halt_turn = main._is_halt_turn
_is_numeric_pick = main._is_numeric_pick


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def live_root(tmp_path: Path):
    """Redirect the live-channel runtime root to a tmp dir for the test.

    ``src.live.paths.live_root`` and ``broker_dir`` both resolve through
    ``get_runtime_root`` at call time, so patching it isolates halt + mandate
    state for halt.py / store.py without touching the real ~/.vibe-trading.
    """
    with patch.object(live_paths, "get_runtime_root", return_value=tmp_path):
        yield tmp_path


def _write_mandate(root: Path, broker: str = "robinhood", *, schema_version: int = 1) -> Path:
    """Write a structurally valid mandate.json under the patched root."""
    broker_dir = root / "live" / broker
    broker_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": schema_version,
        "hard_caps": {
            "account_funding_usd": 5000.0,
            "max_order_notional_usd": 750.0,
            "max_total_exposure_usd": 5000.0,
            "max_leverage": 1.0,
            "allowed_instruments": ["equity"],
            "max_trades_per_day": 5,
        },
        "universe": {
            "asset_classes": ["us_equity"],
            "min_market_cap_usd": None,
            "min_avg_daily_volume_usd": None,
            "exclude_symbols": [],
        },
        "consent": {
            "created_at": "2026-05-29T00:00:00+00:00",
            "consent_token_sha256": "deadbeef",
            "broker": broker,
            "account_ref": "acct_123",
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    }
    path = broker_dir / "mandate.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Subcommand dispatch
# ---------------------------------------------------------------------------


class TestConnectorLiveDispatch:
    def _dispatch(self, argv: list[str]) -> int:
        from cli._legacy import _build_parser, _dispatch_connector

        args = _build_parser().parse_args(argv)
        return _dispatch_connector(args)

    def test_authorize_routes_to_handler(self) -> None:
        with patch("cli._legacy.cmd_connector_authorize", return_value=0) as m:
            assert self._dispatch(["connector", "authorize", "robinhood-live-mcp"]) == 0
        m.assert_called_once_with("robinhood-live-mcp")

    def test_status_routes_with_broker(self) -> None:
        with patch("cli._legacy.cmd_connector_status", return_value=0) as m:
            self._dispatch(["connector", "status", "robinhood-live-mcp"])
        m.assert_called_once_with("robinhood-live-mcp")

    def test_status_routes_default_profile_none(self) -> None:
        with patch("cli._legacy.cmd_connector_status", return_value=0) as m:
            self._dispatch(["connector", "status"])
        m.assert_called_once_with(None)

    def test_halt_routes(self) -> None:
        with patch("cli._legacy.cmd_connector_halt", return_value=0) as m:
            self._dispatch(["connector", "halt"])
        m.assert_called_once_with(None)

    def test_resume_routes(self) -> None:
        with patch("cli._legacy.cmd_connector_resume", return_value=0) as m:
            self._dispatch(["connector", "resume", "robinhood-live-mcp"])
        m.assert_called_once_with("robinhood-live-mcp")

    def test_revoke_routes(self) -> None:
        with patch("cli._legacy.cmd_connector_revoke", return_value=0) as m:
            self._dispatch(["connector", "revoke", "robinhood-live-mcp"])
        m.assert_called_once_with("robinhood-live-mcp")

    def test_no_subcommand_is_usage_error(self) -> None:
        from cli._legacy import EXIT_USAGE_ERROR

        assert self._dispatch(["connector"]) == EXIT_USAGE_ERROR

    def test_no_connector_commit_verb_exists(self) -> None:
        """SPEC: the CLI connector group must not be able to create/widen a mandate."""
        from cli._legacy import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["connector", "commit", "robinhood-live-mcp"])


# ---------------------------------------------------------------------------
# halt / resume on disk
# ---------------------------------------------------------------------------


class TestLiveHaltResume:
    def test_halt_trips_global_sentinel(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_halt
        from src.live.halt import halt_flag_set

        assert cmd_live_halt(None) == 0
        assert (live_root / "live" / "HALT").exists()
        assert halt_flag_set("robinhood") is True

    def test_halt_broker_scoped(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_halt
        from src.live.halt import halt_flag_set

        cmd_live_halt("robinhood")
        assert (live_root / "live" / "robinhood" / "HALT").exists()
        assert not (live_root / "live" / "HALT").exists()
        assert halt_flag_set("robinhood") is True

    def test_resume_clears_halt(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_halt, cmd_live_resume
        from src.live.halt import halt_flag_set

        cmd_live_halt(None)
        assert cmd_live_resume(None) == 0
        assert halt_flag_set("robinhood") is False

    def test_resume_when_not_halted_is_success(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_resume

        assert cmd_live_resume(None) == 0


class TestConnectorHaltResume:
    def test_halt_without_profile_rejects_default_paper_profile(
        self, live_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from cli._legacy import EXIT_USAGE_ERROR, cmd_connector_halt
        from src.trading import profiles

        monkeypatch.setattr(profiles, "get_runtime_root", lambda: live_root)

        assert cmd_connector_halt(None) == EXIT_USAGE_ERROR
        assert not (live_root / "live" / "HALT").exists()

    def test_halt_without_profile_uses_selected_connector(
        self, live_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_connector_halt
        from src.live.halt import halt_flag_set
        from src.trading import profiles

        monkeypatch.setattr(profiles, "get_runtime_root", lambda: live_root)
        profiles.save_selected_profile_id("robinhood-live-mcp")

        assert cmd_connector_halt(None) == 0
        assert (live_root / "live" / "robinhood" / "HALT").exists()
        assert not (live_root / "live" / "HALT").exists()
        assert halt_flag_set("robinhood") is True

        out = capsys.readouterr().out
        assert "vibe-trading connector resume" in out
        assert "vibe-trading live" not in out

    def test_resume_without_profile_uses_selected_connector(
        self, live_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from cli._legacy import cmd_connector_halt, cmd_connector_resume
        from src.live.halt import halt_flag_set
        from src.trading import profiles

        monkeypatch.setattr(profiles, "get_runtime_root", lambda: live_root)
        profiles.save_selected_profile_id("robinhood-live-mcp")

        cmd_connector_halt(None)
        assert cmd_connector_resume(None) == 0
        assert halt_flag_set("robinhood") is False

    def test_halt_with_explicit_non_live_profile_fails(self, live_root: Path) -> None:
        from cli._legacy import EXIT_USAGE_ERROR, cmd_connector_halt

        assert cmd_connector_halt("ibkr-paper-local") == EXIT_USAGE_ERROR
        assert not (live_root / "live" / "HALT").exists()


# ---------------------------------------------------------------------------
# status / mandate (read-only)
# ---------------------------------------------------------------------------


class TestLiveStatusMandate:
    def test_status_no_mandate(self, live_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        from cli._legacy import cmd_live_status

        assert cmd_live_status("robinhood") == 0
        out = capsys.readouterr().out
        assert "none on file" in out

    def test_status_shows_active_mandate_and_countdown(
        self, live_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_live_status

        _write_mandate(live_root)
        cmd_live_status("robinhood")
        out = capsys.readouterr().out
        assert "active" in out
        assert "750" in out  # max order notional
        assert "2099" in out  # expires_at countdown anchor

    def test_status_reflects_halt(self, live_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        from cli._legacy import cmd_live_halt, cmd_live_status

        cmd_live_halt(None)
        cmd_live_status("robinhood")
        assert "HALTED" in capsys.readouterr().out

    def test_status_flags_unknown_schema_version(
        self, live_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_live_status

        _write_mandate(live_root, schema_version=999)
        cmd_live_status("robinhood")
        assert "unknown schema" in capsys.readouterr().out

    def test_mandate_print_no_file(self, live_root: Path) -> None:
        from cli._legacy import EXIT_RUN_FAILED, cmd_live_mandate

        assert cmd_live_mandate("robinhood") == EXIT_RUN_FAILED

    def test_mandate_print_renders_json(
        self, live_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from cli._legacy import cmd_live_mandate

        _write_mandate(live_root)
        assert cmd_live_mandate("robinhood") == 0
        out = capsys.readouterr().out
        assert "max_order_notional_usd" in out
        assert "equity" in out  # enum rendered as string value, not InstrumentType.EQUITY
        assert "InstrumentType" not in out


# ---------------------------------------------------------------------------
# revoke
# ---------------------------------------------------------------------------


class TestLiveRevoke:
    def test_revoke_deletes_token_and_mandate(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_revoke

        broker_dir = live_root / "live" / "robinhood"
        oauth_dir = broker_dir / "oauth"
        oauth_dir.mkdir(parents=True)
        (oauth_dir / "token.json").write_text("{}", encoding="utf-8")
        mandate_path = _write_mandate(live_root)

        # No agent config on disk → _live_server_config returns None → falls back
        # to the canonical broker oauth/ subtree.
        with patch("cli._legacy._live_server_config", return_value=None):
            assert cmd_live_revoke("robinhood") == 0

        assert not oauth_dir.exists()
        assert not mandate_path.exists()

    def test_revoke_nothing_to_remove(self, live_root: Path) -> None:
        from cli._legacy import cmd_live_revoke

        with patch("cli._legacy._live_server_config", return_value=None):
            assert cmd_live_revoke("robinhood") == 0


# ---------------------------------------------------------------------------
# authorize (browser OAuth bootstrap)
# ---------------------------------------------------------------------------


class TestLiveAuthorize:
    def test_authorize_no_config_is_usage_error(self) -> None:
        from cli._legacy import EXIT_USAGE_ERROR, cmd_live_authorize

        with patch("cli._legacy._live_server_config", return_value=None):
            assert cmd_live_authorize("robinhood") == EXIT_USAGE_ERROR

    def test_authorize_triggers_oauth_handshake(self) -> None:
        """The only on-switch: building wrappers forces the connection/OAuth flow."""
        from cli._legacy import cmd_live_authorize

        fake_cfg = type("Cfg", (), {"auth": object()})()
        with patch("cli._legacy._live_server_config", return_value=fake_cfg), patch(
            "src.tools.mcp.build_mcp_tool_wrappers", return_value=[1, 2]
        ) as build:
            assert cmd_live_authorize("robinhood") == 0
        build.assert_called_once()
        assert build.call_args.args[0] == "robinhood"

    def test_authorize_widens_tool_timeout_to_deadline(self) -> None:
        """list_tools is bounded by tool_timeout, so authorize must widen it too.

        Regression for #259: the OAuth flow is driven by the list_tools
        handshake (per-call tool_timeout, default 30 s), not init_timeout. Both
        must reach the 300 s authorize deadline.
        """
        from cli._legacy import cmd_live_authorize
        from src.config.schema import MCPServerConfig

        cfg = MCPServerConfig.model_validate(
            {
                "type": "streamableHttp",
                "url": "https://agent.robinhood.com/mcp/trading",
                "auth": {"type": "oauth", "scopes": ["trading.read"]},
                "enabledTools": ["get_account"],
            }
        )
        with patch("cli._legacy._live_server_config", return_value=cfg), patch(
            "src.tools.mcp.build_mcp_tool_wrappers", return_value=[1]
        ) as build:
            assert cmd_live_authorize("robinhood") == 0

        passed_cfg = build.call_args.args[1]
        assert cfg.tool_timeout == 30  # original unchanged
        assert passed_cfg.init_timeout == 300
        assert passed_cfg.tool_timeout == 300
        # Single attempt: no retry that would orphan the OAuth callback.
        assert build.call_args.kwargs["max_list_tools_attempts"] == 1

    def test_authorize_preserves_larger_configured_tool_timeout(self) -> None:
        """Raise-only: an already-larger configured timeout is not lowered."""
        from cli._legacy import cmd_live_authorize
        from src.config.schema import MCPServerConfig

        cfg = MCPServerConfig.model_validate(
            {
                "type": "streamableHttp",
                "url": "https://agent.robinhood.com/mcp/trading",
                "auth": {"type": "oauth", "scopes": ["trading.read"]},
                "enabledTools": ["get_account"],
                "toolTimeout": 600,
                "initTimeout": 600,
            }
        )
        with patch("cli._legacy._live_server_config", return_value=cfg), patch(
            "src.tools.mcp.build_mcp_tool_wrappers", return_value=[1]
        ) as build:
            assert cmd_live_authorize("robinhood") == 0

        passed_cfg = build.call_args.args[1]
        assert passed_cfg.tool_timeout == 600
        assert passed_cfg.init_timeout == 600

    def test_authorize_honors_timeout_env_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS overrides the 300 s default."""
        from cli._legacy import cmd_live_authorize
        from src.config.schema import MCPServerConfig

        monkeypatch.setenv("VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS", "900")
        cfg = MCPServerConfig.model_validate(
            {
                "type": "streamableHttp",
                "url": "https://agent.robinhood.com/mcp/trading",
                "auth": {"type": "oauth", "scopes": ["trading.read"]},
                "enabledTools": ["get_account"],
            }
        )
        with patch("cli._legacy._live_server_config", return_value=cfg), patch(
            "src.tools.mcp.build_mcp_tool_wrappers", return_value=[1]
        ) as build:
            assert cmd_live_authorize("robinhood") == 0

        passed_cfg = build.call_args.args[1]
        assert passed_cfg.tool_timeout == 900
        assert passed_cfg.init_timeout == 900

    @pytest.mark.parametrize("raw", ["", "abc", "0", "-5"])
    def test_authorize_timeout_env_invalid_falls_back_to_default(
        self, raw: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty / non-numeric / non-positive env values fall back to 300 s."""
        from cli._legacy import _authorize_timeout_seconds

        monkeypatch.setenv("VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS", raw)
        assert _authorize_timeout_seconds() == 300.0


# ---------------------------------------------------------------------------
# REPL intercept helpers
# ---------------------------------------------------------------------------


class TestHaltTurnDetection:
    @pytest.mark.parametrize("text", ["停", "停。", "stop", "STOP", "kill", "halt", " 停 "])
    def test_halt_words(self, text: str) -> None:
        assert _is_halt_turn(text) is True

    @pytest.mark.parametrize(
        "text",
        ["stop the AAPL position", "should I stop trading?", "buy NVDA", "停一下再分析这只票"],
    )
    def test_non_halt_turns(self, text: str) -> None:
        assert _is_halt_turn(text) is False


class TestNumericPick:
    @pytest.mark.parametrize("text,expected", [("1", 1), ("2", 2), (" 3 ", 3), ("2.", 2)])
    def test_bare_pick(self, text: str, expected: int) -> None:
        assert _is_numeric_pick(text) == expected

    @pytest.mark.parametrize("text", ["按 2 但每日笔数提到 10", "option 2", "0", "-1", "two"])
    def test_adjust_or_invalid_not_a_pick(self, text: str) -> None:
        assert _is_numeric_pick(text) is None


# ---------------------------------------------------------------------------
# COMMIT path: pick goes to the endpoint, NEVER the model
# ---------------------------------------------------------------------------


def _proposal() -> Dict[str, Any]:
    return {
        "proposal_id": "mp_" + "3" * 32,
        "session_id": "sess_1",
        "intent_normalized": "aggressive tech, ~$5000",
        "account": {"broker": "robinhood", "type": "cash"},
        "profiles": [
            {"ordinal": 1, "label": "稳健", "max_order_usd": 250, "daily_trade_cap": 2},
            {"ordinal": 2, "label": "均衡", "max_order_usd": 750, "daily_trade_cap": 5},
        ],
    }


class TestProposalPickIntercept:
    def test_numeric_pick_calls_commit_not_model(self) -> None:
        ctx = InteractiveContext()
        ctx.pending_proposal = _proposal()
        commit_result = {"status": "ok", "mandate_id": "mandate_42"}

        with patch.object(main, "_commit_mandate", return_value=commit_result) as commit:
            handled = _handle_proposal_reply("2", ctx)

        assert handled is True  # caller must NOT route to the agent/model
        commit.assert_called_once()
        # The commit binds the exact rendered proposal + the picked ordinal.
        called_proposal, called_ordinal = commit.call_args.args
        assert called_proposal["proposal_id"] == "mp_" + "3" * 32
        assert called_ordinal == 2
        # Successful commit clears the pending proposal.
        assert ctx.pending_proposal is None

    def test_adjust_reply_is_not_intercepted(self) -> None:
        ctx = InteractiveContext()
        ctx.pending_proposal = _proposal()

        with patch.object(main, "_commit_mandate") as commit:
            handled = _handle_proposal_reply("按 2 但每日笔数提到 10", ctx)

        assert handled is False  # caller routes to the agent for a re-render
        commit.assert_not_called()
        # Proposal stays pending until a fresh one replaces it.
        assert ctx.pending_proposal is not None

    def test_out_of_range_pick_does_not_commit(self) -> None:
        ctx = InteractiveContext()
        ctx.pending_proposal = _proposal()

        with patch.object(main, "_commit_mandate") as commit:
            handled = _handle_proposal_reply("9", ctx)

        assert handled is True  # consumed (the model still never sees it)
        commit.assert_not_called()
        assert ctx.pending_proposal is not None  # not cleared on an invalid pick

    def test_commit_failure_keeps_proposal_open(self) -> None:
        ctx = InteractiveContext()
        ctx.pending_proposal = _proposal()

        with patch.object(main, "_commit_mandate", return_value={"status": "error", "error": "boom"}):
            handled = _handle_proposal_reply("1", ctx)

        assert handled is True
        assert ctx.pending_proposal is not None

    def test_commit_posts_to_endpoint_with_consent_ack(self) -> None:
        """_commit_mandate POSTs to /mandate/commit — the surface, not the model."""
        captured: Dict[str, Any] = {}

        class _Resp:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> Dict[str, Any]:
                return {"status": "ok", "mandate_id": "m1"}

        def _fake_post(url: str, json: Dict[str, Any], timeout: float) -> _Resp:  # noqa: A002
            captured["url"] = url
            captured["body"] = json
            return _Resp()

        with patch("httpx.post", _fake_post):
            result = _commit_mandate(_proposal(), 2)

        assert result["mandate_id"] == "m1"
        assert captured["url"].endswith("/mandate/commit")
        assert captured["body"]["selected_ordinal"] == 2
        assert captured["body"]["proposal_id"] == "mp_" + "3" * 32
        assert captured["body"]["consent_ack"] is True


# ---------------------------------------------------------------------------
# Kill-switch intercept: trips the flag without the agent loop
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ARMING path: a REAL propose-tool tool_result event through on_event arms
# ctx.pending_proposal (closes the false-confidence gap — prior tests set
# pending_proposal directly and never exercised the relay). SPEC Consent §1/§2.
# ---------------------------------------------------------------------------


def _write_proposal_to_disk(root: Path, proposal_id: str, broker: str = "robinhood") -> Dict[str, Any]:
    """Persist a full mandate.proposal exactly as ``propose_mandate_profiles`` does.

    The propose tool writes ``<runtime_root>/live/<broker>/proposals/<id>.json``;
    the relay reloads from there because the tool_result preview is truncated.
    """
    proposals_dir = root / "live" / broker / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "type": "mandate.proposal",
        "proposal_id": proposal_id,
        "session_id": "sess_1",
        "intent_normalized": "aggressive tech, ~$5000",
        "account": {"broker": broker, "type": "cash"},
        "profiles": [
            {"ordinal": 1, "label": "稳健", "max_order_usd": 250, "daily_trade_cap": 2},
            {"ordinal": 2, "label": "均衡", "max_order_usd": 750, "daily_trade_cap": 5},
        ],
    }
    (proposals_dir / f"{proposal_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _capture_on_event(captured: Dict[str, Any]):
    """Run ``_run_agent`` with all heavy deps stubbed, returning its ``on_event``.

    Replaces ``AgentLoop`` with a stub that captures the real ``event_callback``
    closure (``on_event``) instead of running an LLM, so a test can replay
    arbitrary events THROUGH the genuine relay logic. ``build_registry`` /
    ``ChatLLM`` / ``PersistentMemory`` / ``load_agent_config`` are stubbed to
    no-ops so nothing touches the network or disk beyond the proposal reload.
    """
    import types as _types

    from cli import _legacy

    class _StubLoop:
        def __init__(self, *_, event_callback=None, **__):
            captured["on_event"] = event_callback
            self.memory = _types.SimpleNamespace(run_dir=None)

        def run(self, **__):
            return {"content": "ok"}

    proposal_seen: Dict[str, Any] = {}

    def _sink(payload: Dict[str, Any]) -> None:
        proposal_seen.clear()
        proposal_seen.update(payload)

    captured["sink_result"] = proposal_seen

    # ``_run_agent`` does local ``from ... import`` for these, so patch the
    # SOURCE modules, not the ``cli._legacy`` namespace.
    with patch("src.agent.loop.AgentLoop", _StubLoop), patch(
        "src.tools.build_registry", return_value=object()
    ), patch("src.providers.chat.ChatLLM", lambda *a, **k: object()), patch(
        "src.memory.persistent.PersistentMemory",
        lambda *a, **k: _types.SimpleNamespace(run_dir=None),
    ), patch(
        "src.config.loader.load_agent_config", return_value=object()
    ):
        _legacy._run_agent(
            "let AI trade tech aggressively with $5000",
            stream_output=False,
            proposal_sink=_sink,
        )
    return captured["on_event"]


class TestProposalArmingRelay:
    def test_real_tool_result_event_arms_pending_proposal(self, live_root: Path) -> None:
        """A genuine propose-tool tool_result through on_event arms the proposal.

        This is the path the prior tests skipped (they set pending_proposal
        directly). Drives the event THROUGH the real ``on_event`` relay and
        asserts the full proposal is reloaded from disk into the sink.
        """
        proposal_id = "mp_" + "4" * 32
        _write_proposal_to_disk(live_root, proposal_id)

        captured: Dict[str, Any] = {}
        on_event = _capture_on_event(captured)
        assert on_event is not None

        # The agent loop emits ONLY a generic tool_result; preview = result[:200]
        # of the JSON body, which carries the proposal_id near the front.
        preview = json.dumps(
            {"type": "mandate.proposal", "proposal_id": proposal_id, "session_id": "sess_1"}
        )[:200]
        on_event("tool_result", {"tool": "propose_mandate_profiles", "status": "ok", "preview": preview})

        armed = captured["sink_result"]
        assert armed.get("proposal_id") == proposal_id
        assert armed.get("type") == "mandate.proposal"
        # Full body reloaded from disk — profiles the preview never carried.
        assert [p["ordinal"] for p in armed["profiles"]] == [1, 2]

    def test_unrelated_tool_result_does_not_arm(self, live_root: Path) -> None:
        """A non-propose tool_result must never arm a proposal (no false-positive)."""
        captured: Dict[str, Any] = {}
        on_event = _capture_on_event(captured)
        on_event("tool_result", {"tool": "backtest", "status": "ok", "preview": '{"sharpe": 1.2}'})
        assert captured["sink_result"] == {}

    def test_armed_then_bare_2_is_intercepted_not_sent_to_model(self, live_root: Path) -> None:
        """End-to-end: arm via the relay, then a bare '2' commits (model never sees it).

        Mirrors ``_interactive_loop``'s interception order: halt → proposal pick
        → slash → model. With a proposal armed, '2' is consumed by
        ``_handle_proposal_reply`` and routed to the commit endpoint, NOT the
        agent.
        """
        proposal_id = "mp_" + "5" * 32
        _write_proposal_to_disk(live_root, proposal_id)

        # 1) Arm through the real relay.
        captured: Dict[str, Any] = {}
        on_event = _capture_on_event(captured)
        preview = json.dumps({"type": "mandate.proposal", "proposal_id": proposal_id})[:200]
        on_event("tool_result", {"tool": "propose_mandate_profiles", "status": "ok", "preview": preview})

        ctx = InteractiveContext()
        ctx.pending_proposal = dict(captured["sink_result"])
        assert ctx.pending_proposal["proposal_id"] == proposal_id

        # 2) A bare "2" is intercepted BEFORE the model: replicate the loop guard.
        text = "2"
        routed_to_model = {"called": False}

        def _fake_run_turn(*_a, **_k) -> None:
            routed_to_model["called"] = True

        with patch.object(main, "_run_one_turn", _fake_run_turn), patch.object(
            main, "_commit_mandate", return_value={"status": "ok", "mandate_id": "m99"}
        ) as commit, patch.object(main, "_is_halt_turn", return_value=False):
            handled = False
            if main._is_halt_turn(text):
                pass
            elif ctx.pending_proposal is not None and not text.startswith("/"):
                handled = main._handle_proposal_reply(text, ctx)
            if not handled and not text.startswith("/"):
                main._run_one_turn(text, ctx)

        assert handled is True
        assert routed_to_model["called"] is False  # the model NEVER saw the pick
        commit.assert_called_once()
        assert commit.call_args.args[0]["proposal_id"] == proposal_id
        assert commit.call_args.args[1] == 2
        assert ctx.pending_proposal is None  # cleared on a successful commit

    def test_bare_2_with_no_pending_proposal_routes_to_model(self, live_root: Path) -> None:
        """No proposal armed → a bare '2' is normal text and goes to the model.

        Guards against the relay over-reaching: the interception only fires when
        ``ctx.pending_proposal`` is set; otherwise '2' must reach the agent.
        """
        ctx = InteractiveContext()
        assert ctx.pending_proposal is None

        text = "2"
        routed_to_model = {"called": False}

        def _fake_run_turn(arg_text: str, _ctx) -> None:
            routed_to_model["called"] = True
            assert arg_text == "2"

        with patch.object(main, "_run_one_turn", _fake_run_turn), patch.object(
            main, "_handle_proposal_reply"
        ) as handle, patch.object(main, "_is_halt_turn", return_value=False):
            handled = False
            if main._is_halt_turn(text):
                pass
            elif ctx.pending_proposal is not None and not text.startswith("/"):
                handled = main._handle_proposal_reply(text, ctx)
            if not handled and not text.startswith("/"):
                main._run_one_turn(text, ctx)

        handle.assert_not_called()  # no proposal → interception never runs
        assert routed_to_model["called"] is True  # '2' reached the model as chat


class TestHaltIntercept:
    def test_repl_halt_trips_flag(self, live_root: Path) -> None:
        from src.live.halt import halt_flag_set

        console = main.get_console()
        main._trip_halt_from_repl(console, reason="repl turn: 停")

        assert halt_flag_set("robinhood") is True
        assert (live_root / "live" / "HALT").exists()

    def test_halt_turn_bypasses_one_turn_runner(self, live_root: Path) -> None:
        """A bare halt turn trips the switch via the input path, never the agent.

        Mirrors the ``_interactive_loop`` guard: a halt turn is consumed before
        ``_run_one_turn`` (the only path into ``_run_agent``) is ever called.
        """
        from src.live.halt import halt_flag_set

        text = "停"
        ctx = InteractiveContext()
        console = main.get_console()

        with patch.object(main, "_run_one_turn") as run_turn:
            # Replicate the loop's interception order: halt check comes first.
            if _is_halt_turn(text):
                main._trip_halt_from_repl(console, reason=f"repl turn: {text}")
            else:
                run_turn(text, ctx)

        run_turn.assert_not_called()
        assert halt_flag_set("robinhood") is True
