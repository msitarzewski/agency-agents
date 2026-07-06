"""Kill switch blocks live orders at the gate (SPEC.md Consent §4, gate-level).

With a committed mandate and the HALT flag set, ``LiveOrderGuardTool.execute``
must return a refusal and make NO remote call (the mock adapter's order tool is
never invoked). Read tools are unaffected by HALT — only the gate refuses.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import src.live.paths as paths
from src.live.halt import trip_halt
from src.live.mandate.model import (
    MANDATE_SCHEMA_VERSION,
    AssetClass,
    ConsentMeta,
    HardCaps,
    InstrumentType,
    Mandate,
    UniverseConstraint,
)
from src.live.order_guard import LiveOrderGuardTool
from src.tools.mcp import MCPRemoteTool, MCPRemoteToolSpec


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


class _MockAdapter:
    def __init__(self) -> None:
        self.server_name = "robinhood"
        self.calls: list[str] = []

    def call_tool(self, remote_name: str, arguments: dict, *, local_name: str | None = None) -> dict:
        self.calls.append(remote_name)
        if remote_name in ("get_positions", "list_positions"):
            return {"positions": [], "status": "ok"}
        if remote_name in ("get_account", "get_balance", "get_buying_power"):
            return {"equity": 5000.0, "status": "ok"}
        return {"status": "ok", "order_id": "rh_x", "state": "accepted"}


def _order_spec() -> MCPRemoteToolSpec:
    return MCPRemoteToolSpec(
        server_name="robinhood",
        remote_name="place_order",
        local_name="mcp_robinhood_place_order",
        description="Place an order.",
        parameters={"type": "object", "properties": {}, "additionalProperties": True},
    )


def _read_spec() -> MCPRemoteToolSpec:
    return MCPRemoteToolSpec(
        server_name="robinhood",
        remote_name="get_positions",
        local_name="mcp_robinhood_get_positions",
        description="Read positions.",
        parameters={"type": "object", "properties": {}, "additionalProperties": True},
    )


def _write_mandate(live_runtime: Path) -> None:
    broker = live_runtime / "live" / "robinhood"
    broker.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    payload = {
        "schema_version": MANDATE_SCHEMA_VERSION,
        "hard_caps": {
            "account_funding_usd": 5000.0,
            "max_order_notional_usd": 750.0,
            "max_total_exposure_usd": 5000.0,
            "max_leverage": 1.0,
            "allowed_instruments": ["equity", "etf"],
            "max_trades_per_day": 5,
        },
        "universe": {
            "asset_classes": ["us_equity", "us_etf"],
            "min_market_cap_usd": None,
            "min_avg_daily_volume_usd": None,
            "exclude_symbols": [],
        },
        "consent": {
            "created_at": created.isoformat(),
            "consent_token_sha256": "deadbeef",
            "broker": "robinhood",
            "account_ref": "acct_ref",
            "expires_at": (created + timedelta(days=30)).isoformat(),
        },
    }
    (broker / "mandate.json").write_text(json.dumps(payload), encoding="utf-8")


def test_halt_blocks_order_no_remote_call(live_runtime: Path) -> None:
    _write_mandate(live_runtime)
    trip_halt(by="file", reason="test halt")  # global sentinel
    adapter = _MockAdapter()
    guard = LiveOrderGuardTool(adapter, _order_spec(), broker="robinhood", session_id="s1")

    out = json.loads(
        guard.execute(symbol="AAPL", side="buy", instrument_type="equity", notional_usd=100.0)
    )

    assert out["status"] == "blocked"
    assert out["decision"] == "deny"
    assert "halt" in out["reason"].lower()
    # No remote call of ANY kind — the gate short-circuits before reading.
    assert adapter.calls == []


def test_per_broker_halt_blocks_order(live_runtime: Path) -> None:
    _write_mandate(live_runtime)
    trip_halt(by="cli", reason="broker halt", broker="robinhood")
    adapter = _MockAdapter()
    guard = LiveOrderGuardTool(adapter, _order_spec(), broker="robinhood", session_id="s1")

    out = json.loads(
        guard.execute(symbol="AAPL", side="buy", instrument_type="equity", notional_usd=100.0)
    )
    assert out["status"] == "blocked"
    assert adapter.calls == []


def test_read_tools_unaffected_by_halt(live_runtime: Path) -> None:
    """A plain read tool is NOT a guard — HALT must not block reads."""
    _write_mandate(live_runtime)
    trip_halt(by="file", reason="test halt")
    adapter = _MockAdapter()
    read_tool = MCPRemoteTool(adapter, _read_spec())

    payload = json.loads(read_tool.execute())
    assert payload["status"] == "ok"
    assert adapter.calls == ["get_positions"]
