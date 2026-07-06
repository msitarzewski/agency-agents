"""Unit tests for the local IBKR TWS / IB Gateway bridge."""

from __future__ import annotations

import json
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.trading.connectors.ibkr import local
from src.tools.trading_connector_tool import TradingPositionsTool

pytestmark = pytest.mark.unit


class _FakeContract:
    def __init__(self) -> None:
        self.symbol = ""
        self.secType = ""
        self.exchange = ""
        self.currency = ""
        self.conId = 0
        self.localSymbol = ""


class _FakeStock(_FakeContract):
    def __init__(self, symbol: str, exchange: str, currency: str) -> None:
        super().__init__()
        self.symbol = symbol
        self.secType = "STK"
        self.exchange = exchange
        self.currency = currency
        self.conId = 101
        self.localSymbol = symbol


class _FakeIB:
    def connect(self, host, port, *, clientId, timeout, readonly=True, account=""):
        self.host = host
        self.port = port
        self.client_id = clientId
        self.readonly = readonly
        self.account = account

    def disconnect(self):
        self.disconnected = True

    def managedAccounts(self):
        return ["DU12345"]

    def accountSummary(self, account=""):
        return [
            SimpleNamespace(account="DU12345", tag="NetLiquidation", value="100000", currency="USD", modelCode="")
        ]

    def positions(self):
        contract = SimpleNamespace(
            symbol="AAPL",
            localSymbol="AAPL",
            secType="STK",
            exchange="SMART",
            currency="USD",
            conId=265598,
        )
        return [SimpleNamespace(account="DU12345", contract=contract, position=3, avgCost=150.0)]

    def openTrades(self):
        return []

    def qualifyContracts(self, contract):
        return [contract]

    def reqMktData(self, contract, genericTickList, snapshot, regulatorySnapshot):
        return SimpleNamespace(bid=100.0, ask=100.2, last=100.1, close=99.0, volume=1234, time="")

    def cancelMktData(self, contract):
        return None

    def sleep(self, seconds):
        return None

    def reqHistoricalData(
        self,
        contract,
        *,
        endDateTime,
        durationStr,
        barSizeSetting,
        whatToShow,
        useRTH,
        formatDate,
    ):
        return [SimpleNamespace(date="2026-05-29", open=1, high=2, low=0.5, close=1.5, volume=100)]


@pytest.fixture()
def fake_ib_async(monkeypatch: pytest.MonkeyPatch):
    module = types.ModuleType("ib_async")
    module.IB = _FakeIB
    module.Stock = _FakeStock
    module.Contract = _FakeContract
    monkeypatch.setitem(sys.modules, "ib_async", module)
    monkeypatch.setattr(local, "tcp_port_open", lambda *_, **__: True)
    return module


def test_config_defaults_to_paper_port() -> None:
    cfg = local.IBKRLocalConfig.from_mapping({"profile": "paper"})
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 7497
    assert cfg.readonly is True


def test_account_snapshot_reads_summary(fake_ib_async) -> None:
    cfg = local.IBKRLocalConfig()
    result = local.get_account_snapshot(cfg)

    assert result["status"] == "ok"
    assert result["accounts"] == ["DU12345"]
    assert result["summary"][0]["tag"] == "NetLiquidation"


def test_positions_are_serialized(fake_ib_async) -> None:
    result = local.get_positions(local.IBKRLocalConfig())

    assert result["positions"][0]["symbol"] == "AAPL"
    assert result["positions"][0]["position"] == 3


def test_quote_and_history_are_readonly(fake_ib_async) -> None:
    quote = local.get_quote("AAPL", config=local.IBKRLocalConfig())
    history = local.get_historical_bars("AAPL", config=local.IBKRLocalConfig())

    assert quote["quote"]["last"] == 100.1
    assert history["bars"][0]["close"] == 1.5


def test_paper_profile_rejects_live_account(monkeypatch: pytest.MonkeyPatch, fake_ib_async) -> None:
    class _LiveIB(_FakeIB):
        def managedAccounts(self):
            return ["U12345"]

        def accountSummary(self, account=""):
            return [SimpleNamespace(account="U12345", tag="NetLiquidation", value="1", currency="USD", modelCode="")]

    fake_ib_async.IB = _LiveIB

    with pytest.raises(local.IBKRProfileMismatchError):
        local.get_account_snapshot(local.IBKRLocalConfig(profile="paper"))


def test_check_status_reports_missing_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local, "ib_async_available", lambda: False)
    monkeypatch.setattr(local, "tcp_port_open", lambda *_, **__: True)

    report = local.check_local_status(local.IBKRLocalConfig(), scan=False)

    assert report["status"] == "error"
    assert "ib_async" in report["error"]


def test_positions_tool_returns_json(fake_ib_async) -> None:
    payload = json.loads(TradingPositionsTool().execute(connection="ibkr-paper-local"))

    assert payload["status"] == "ok"
    assert payload["profile_id"] == "ibkr-paper-local"
    assert payload["positions"][0]["symbol"] == "AAPL"


def test_service_uses_persisted_ibkr_local_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Configured local endpoint values must survive later connector calls."""
    from src.trading import service

    monkeypatch.setattr(local, "get_runtime_root", lambda: tmp_path)
    local.save_config(
        local.IBKRLocalConfig(
            profile="paper",
            host="192.168.10.8",
            port=4002,
            client_id=123,
            account="DU999",
        )
    )
    captured: dict[str, local.IBKRLocalConfig] = {}

    def _check(cfg: local.IBKRLocalConfig) -> dict[str, object]:
        captured["cfg"] = cfg
        return {"status": "ok", "ports": [], "target": {}, "sdk": {"installed": True}}

    monkeypatch.setattr(local, "check_local_status", _check)

    assert service.check_connection("ibkr-paper-local")["status"] == "ok"

    cfg = captured["cfg"]
    assert cfg.host == "192.168.10.8"
    assert cfg.port == 4002
    assert cfg.client_id == 123
    assert cfg.account == "DU999"


def test_cli_connector_routes_to_handler() -> None:
    from cli._legacy import _build_parser, _dispatch_connector

    args = _build_parser().parse_args(["connector", "check", "ibkr-paper-local", "--account", "DU12345"])
    with patch("cli._legacy.cmd_connector_check", return_value=0) as handler:
        assert _dispatch_connector(args) == 0
    handler.assert_called_once_with(
        "ibkr-paper-local",
        host=None,
        port=None,
        client_id=None,
        account="DU12345",
    )


def test_cli_connector_check_passes_account_to_backend() -> None:
    from cli._legacy import cmd_connector_check

    report = {"status": "ok", "ports": [], "target": {}, "sdk": {"installed": True}}
    with patch("src.trading.service.check_connection", return_value=report) as check:
        assert cmd_connector_check("ibkr-paper-local", account="DU12345") == 0
    check.assert_called_once_with(
        "ibkr-paper-local",
        host=None,
        port=None,
        client_id=None,
        account="DU12345",
    )
