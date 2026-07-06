"""Tests for the direct-SDK live order gate + service order routing (Layer B/C).

The gate is the red-line code: live orders must pass mandate + kill-switch +
fail-closed pre-trade checks before any broker call. These tests use a fake
connector module + a stubbed mandate/halt so they need no broker SDK.
"""

from __future__ import annotations

import pytest

from src.live import sdk_order_gate as gate
from src.live.enforcement import OrderIntent
from src.live.mandate.model import (
    AssetClass,
    ConsentMeta,
    HardCaps,
    InstrumentType,
    Mandate,
    UniverseConstraint,
)
from src.trading import service

pytestmark = pytest.mark.unit


class _FakeConnector:
    """Minimal connector module stand-in capturing place_order calls."""

    def __init__(self, *, positions=None, balance=None, quote_last=100.0):
        self.placed: list[dict] = []
        self._positions = positions if positions is not None else {"status": "ok", "positions": []}
        self._balance = balance if balance is not None else {"status": "ok", "account": {}}
        self._quote_last = quote_last

    def place_order(self, config, **kwargs):
        self.placed.append(kwargs)
        return {"status": "ok", "order_id": "OID-1", **kwargs}

    def get_positions(self, config):
        return self._positions

    def get_account_snapshot(self, config):
        return self._balance

    def get_quote(self, symbol, *, config=None):
        return {"status": "ok", "symbol": symbol, "quote": {"last": self._quote_last}}


def _mandate(*, max_order=1_000_000.0, assets=(AssetClass.US_EQUITY,), instruments=(InstrumentType.EQUITY,)):
    return Mandate(
        schema_version=1,
        hard_caps=HardCaps(
            account_funding_usd=1_000_000.0,
            max_order_notional_usd=max_order,
            max_total_exposure_usd=1_000_000.0,
            max_leverage=2.0,
            allowed_instruments=tuple(instruments),
            max_trades_per_day=100,
        ),
        universe=UniverseConstraint(
            asset_classes=tuple(assets),
            min_market_cap_usd=None,
            min_avg_daily_volume_usd=None,
            exclude_symbols=(),
        ),
        consent=ConsentMeta(
            created_at="2026-01-01T00:00:00+00:00",
            consent_token_sha256="deadbeef",
            broker="alpaca",
            account_ref="acct-1",
            expires_at="2999-01-01T00:00:00+00:00",
        ),
    )


def _patch_gate(monkeypatch, *, mandate, halted=False):
    monkeypatch.setattr(gate, "load_mandate", lambda broker: mandate)
    monkeypatch.setattr(gate, "halt_flag_set", lambda broker: halted)
    monkeypatch.setattr(gate, "write_live_action", lambda *a, **k: {"audited": True})
    monkeypatch.setattr(gate, "read_daily_count", lambda broker: 0)
    monkeypatch.setattr(gate, "increment_daily_count", lambda broker: 1)


def _intent(notional=500.0, qty=None, asset=AssetClass.US_EQUITY):
    return OrderIntent(
        symbol="AAPL", side="buy", notional_usd=notional, quantity=qty,
        instrument_type=InstrumentType.EQUITY, asset_class=asset,
    )


# --------------------------------------------------------------------------- #
# Gate decisions
# --------------------------------------------------------------------------- #


def test_gate_denies_without_mandate(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=None)
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "blocked" and out["decision"] == "deny"
    assert "mandate" in out["reason"]
    assert conn.placed == []  # never reached the broker


def test_gate_denies_on_halt(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_mandate(), halted=True)
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "blocked"
    assert "halt" in out["reason"].lower()
    assert conn.placed == []


def test_gate_allows_in_bounds_and_places(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_mandate())
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(notional=500.0), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "ok" and out["order_id"] == "OID-1"
    assert len(conn.placed) == 1  # forwarded to broker
    assert "live_action" in out


def test_gate_blocks_oversized_order(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_mandate(max_order=100.0))
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(notional=5000.0), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 5000.0},
    )
    assert out["status"] == "blocked"
    assert out["decision"] in ("pause_for_reauth", "deny")
    assert conn.placed == []  # breach → never placed


def test_gate_blocks_disallowed_asset_class(monkeypatch) -> None:
    # Mandate allows only US equity; an HK-equity order must be denied structurally.
    _patch_gate(monkeypatch, mandate=_mandate(assets=(AssetClass.US_EQUITY,)))
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="tiger", connector_module=conn, config=object(),
        intent=_intent(asset=AssetClass.HK_EQUITY),
        place_kwargs={"symbol": "700.HK", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "blocked" and out["decision"] == "deny"
    assert conn.placed == []


def test_gate_quantity_order_priced_and_enforced(monkeypatch) -> None:
    # quantity-only order: gate prices via connector quote (last=100) → 10*100=1000 notional.
    _patch_gate(monkeypatch, mandate=_mandate(max_order=500.0))
    conn = _FakeConnector(quote_last=100.0)
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(notional=None, qty=10.0),
        place_kwargs={"symbol": "AAPL", "side": "buy", "quantity": 10.0},
    )
    # 1000 > max_order 500 → blocked
    assert out["status"] == "blocked"
    assert conn.placed == []


# --------------------------------------------------------------------------- #
# Service routing
# --------------------------------------------------------------------------- #


def test_service_place_order_paper_is_direct(monkeypatch) -> None:
    """Paper profile places directly (sandbox), bypassing the live gate."""
    conn = _FakeConnector()
    monkeypatch.setattr(service, "_sdk_module", lambda c: conn)
    monkeypatch.setattr(conn, "build_config", lambda *a, **k: object(), raising=False)
    # build_config is called on the module; give the fake one.
    conn.build_config = lambda profile_config, overrides: object()
    out = service.place_order("AAPL", "alpaca-paper-trade", side="buy", quantity=1)
    assert out["status"] == "ok"
    assert len(conn.placed) == 1
    assert out["environment"] == "paper"


def test_service_place_order_live_routes_through_gate(monkeypatch) -> None:
    """Live profile routes through the gate; no mandate → blocked, not placed."""
    conn = _FakeConnector()
    conn.build_config = lambda profile_config, overrides: object()
    monkeypatch.setattr(service, "_sdk_module", lambda c: conn)
    monkeypatch.setattr("src.live.sdk_order_gate.load_mandate", lambda broker: None)
    monkeypatch.setattr("src.live.sdk_order_gate.write_live_action", lambda *a, **k: {"audited": True})
    out = service.place_order("AAPL", "alpaca-live-trade", side="buy", notional=500.0)
    assert out["status"] == "blocked"
    assert conn.placed == []
    assert out["environment"] == "live"


def test_no_longbridge_live_trade_profile() -> None:
    from src.trading import profiles

    ids = {p.id for p in profiles.list_profiles()}
    assert "longbridge-paper-trade" in ids
    assert "longbridge-live-trade" not in ids  # capped: no live order placement


def test_trade_profiles_have_place_capability() -> None:
    from src.trading import profiles

    for pid in ("alpaca-live-trade", "okx-live-trade", "binance-live-trade", "futu-live-trade", "tiger-live-trade"):
        prof = profiles.profile_by_id(pid)
        assert prof.readonly is False
        assert any("requires_mandate" in c for c in prof.capabilities)


# --------------------------------------------------------------------------- #
# Gate edges: expiry, count-only-on-success, connector raise, unpriceable qty
# --------------------------------------------------------------------------- #


def _expired_mandate():
    m = _mandate()
    return Mandate(
        schema_version=1, hard_caps=m.hard_caps, universe=m.universe,
        consent=ConsentMeta(
            created_at="2020-01-01T00:00:00+00:00", consent_token_sha256="x",
            broker="alpaca", account_ref="a", expires_at="2020-02-01T00:00:00+00:00",
        ),
    )


def test_gate_denies_expired_mandate(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_expired_mandate())
    conn = _FakeConnector()
    out = gate.execute_live_order(
        broker="alpaca", connector_module=conn, config=object(),
        intent=_intent(), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "blocked" and out["requires_reauthorization"] is True
    assert conn.placed == []


def test_gate_count_consumed_only_on_success(monkeypatch) -> None:
    increments: list[str] = []
    monkeypatch.setattr(gate, "load_mandate", lambda b: _mandate())
    monkeypatch.setattr(gate, "halt_flag_set", lambda b: False)
    monkeypatch.setattr(gate, "write_live_action", lambda *a, **k: {"audited": True})
    monkeypatch.setattr(gate, "read_daily_count", lambda b: 0)
    monkeypatch.setattr(gate, "increment_daily_count", lambda b: increments.append(b))

    # Connector returns an error envelope → no count consumed.
    class _ErrConn(_FakeConnector):
        def place_order(self, config, **kwargs):
            return {"status": "error", "error": "broker rejected"}

    out = gate.execute_live_order(
        broker="alpaca", connector_module=_ErrConn(), config=object(),
        intent=_intent(), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "error"
    assert increments == []  # failed placement must not consume a daily count


def test_gate_connector_raise_is_caught(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_mandate())

    class _RaiseConn(_FakeConnector):
        def place_order(self, config, **kwargs):
            raise RuntimeError("sdk boom")

    out = gate.execute_live_order(
        broker="alpaca", connector_module=_RaiseConn(), config=object(),
        intent=_intent(), place_kwargs={"symbol": "AAPL", "side": "buy", "notional": 500.0},
    )
    assert out["status"] == "error"  # raise converted to error envelope, not propagated


def test_gate_quantity_unpriceable_denies(monkeypatch) -> None:
    _patch_gate(monkeypatch, mandate=_mandate())

    class _NoQuoteConn(_FakeConnector):
        def get_quote(self, symbol, *, config=None):
            return {"status": "error", "error": "no quote"}

    # Force the loader fallback to also fail so pricing is impossible.
    monkeypatch.setattr("src.live.sdk_order_gate.last_price_usd", lambda *a, **k: None)
    out = gate.execute_live_order(
        broker="alpaca", connector_module=_NoQuoteConn(), config=object(),
        intent=_intent(notional=None, qty=5.0),
        place_kwargs={"symbol": "AAPL", "side": "buy", "quantity": 5.0},
    )
    assert out["status"] == "blocked" and "priced" in out["reason"]


# --------------------------------------------------------------------------- #
# Connector order-method validation (fail-closed, no SDK needed)
# --------------------------------------------------------------------------- #


def test_longbridge_place_order_paper_only_guard() -> None:
    from src.trading.connectors.longbridge import sdk as lb

    cfg = lb.LongbridgeConfig(app_key="k", app_secret="s", access_token="t", profile="live-readonly")
    out = lb.place_order(cfg, symbol="700.HK", side="buy", quantity=100)
    assert out["status"] == "error" and "paper" in out["error"].lower()
    out2 = lb.cancel_order(cfg, "OID", symbol="700.HK")
    assert out2["status"] == "error" and "paper" in out2["error"].lower()


@pytest.mark.parametrize("connector", ["tiger", "alpaca", "okx", "binance", "futu", "longbridge"])
def test_connector_place_order_rejects_bad_side(connector) -> None:
    import importlib

    mod = importlib.import_module(f"src.trading.connectors.{connector}.sdk")
    cfg = mod.build_config({"profile": "paper"}, None)
    out = mod.place_order(cfg, symbol="AAPL", side="hold", quantity=1)
    assert out["status"] == "error"


@pytest.mark.parametrize("connector", ["tiger", "alpaca", "okx", "binance", "futu", "longbridge"])
def test_connector_place_order_rejects_both_qty_and_notional(connector) -> None:
    import importlib

    mod = importlib.import_module(f"src.trading.connectors.{connector}.sdk")
    cfg = mod.build_config({"profile": "paper"}, None)
    out = mod.place_order(cfg, symbol="AAPL", side="buy", quantity=1, notional=100)
    assert out["status"] == "error"


def test_okx_order_result_rejects_failed_scode() -> None:
    from src.trading.connectors.okx import sdk as ox

    cfg = ox.OKXConfig(api_key="k", api_secret="s", passphrase="p")
    # A 200 envelope (code 0) whose per-order sCode != 0 is a FAILED order.
    failed = ox._order_result(cfg, {"code": "0", "data": [{"sCode": "51008", "sMsg": "insufficient"}]}, symbol="BTC-USDT", side="buy", order_type="market", time_in_force="day")
    assert failed["status"] == "error"
    ok = ox._order_result(cfg, {"code": "0", "data": [{"ordId": "O1", "sCode": "0"}]}, symbol="BTC-USDT", side="buy", order_type="market", time_in_force="day")
    assert ok["status"] == "ok" and ok["order_id"] == "O1"
