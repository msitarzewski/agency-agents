"""Tests for the preemptive kill-switch sweep (src/live/runtime/flatten.py).

SPEC §7.5 component 6. Verifies cancel-then-flatten ordering, the cancel-only
default when the mandate forbids flatten, the no-retry-on-error contract
(SPEC §8.5), and that every broker call is audited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.live import audit, paths
from src.live.runtime import flatten


class _Broker:
    """In-memory broker stub recording the order of injected calls."""

    def __init__(
        self,
        open_orders: list[dict[str, Any]],
        positions: list[dict[str, Any]],
        fail_on: set[str] | None = None,
    ) -> None:
        self._open_orders = open_orders
        self._positions = positions
        self._fail_on = fail_on or set()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def read_open_orders(self) -> list[dict[str, Any]]:
        return list(self._open_orders)

    def read_positions(self) -> list[dict[str, Any]]:
        return list(self._positions)

    def submit(self, request: dict[str, Any]) -> dict[str, Any]:
        action = request.get("action", "")
        key = request.get("order_id") or request.get("symbol") or action
        self.calls.append((action, request))
        if key in self._fail_on:
            raise RuntimeError(f"broker rejected {key}")
        return {"state": "accepted", "echo": key}


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live runtime root at an isolated tmp dir."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def _read_ledger() -> list[dict[str, Any]]:
    path = audit.audit_ledger_path()
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_cancel_only_default_when_mandate_absent(live_runtime: Path) -> None:
    # No mandate on file → fail-closed to cancel-only; positions untouched.
    broker = _Broker(
        open_orders=[{"order_id": "o1"}, {"order_id": "o2"}],
        positions=[{"symbol": "NVDA", "qty": 3}],
    )
    report = flatten.flatten_and_cancel(
        "robinhood", broker.submit, broker.read_positions, broker.read_open_orders
    )
    assert report["cancelled_order_ids"] == ["o1", "o2"]
    assert report["flatten_orders_submitted"] == []
    assert report["flatten_skipped_reason"] is not None
    # Only cancels were submitted — no flatten/close calls.
    assert all(action == "cancel" for action, _ in broker.calls)


def test_cancel_then_flatten_order(live_runtime: Path) -> None:
    broker = _Broker(
        open_orders=[{"order_id": "o1"}],
        positions=[{"symbol": "NVDA", "qty": 3}, {"symbol": "AAPL", "qty": -2}],
    )
    report = flatten.flatten_and_cancel(
        "robinhood",
        broker.submit,
        broker.read_positions,
        broker.read_open_orders,
        allow_flatten=True,
    )
    # Cancels MUST precede flattens.
    actions = [action for action, _ in broker.calls]
    assert actions == ["cancel", "close", "close"]
    assert report["cancelled_order_ids"] == ["o1"]
    submitted = report["flatten_orders_submitted"]
    # Long closed by sell, short closed by buy.
    by_symbol = {s["symbol"]: s for s in submitted}
    assert by_symbol["NVDA"]["side"] == "sell" and by_symbol["NVDA"]["qty"] == 3
    assert by_symbol["AAPL"]["side"] == "buy" and by_symbol["AAPL"]["qty"] == 2
    assert report["flatten_skipped_reason"] is None


def test_zero_qty_position_skipped(live_runtime: Path) -> None:
    broker = _Broker(open_orders=[], positions=[{"symbol": "GME", "qty": 0}])
    report = flatten.flatten_and_cancel(
        "robinhood",
        broker.submit,
        broker.read_positions,
        broker.read_open_orders,
        allow_flatten=True,
    )
    assert report["flatten_orders_submitted"] == []
    assert broker.calls == []


def test_errored_cancel_is_not_retried(live_runtime: Path) -> None:
    broker = _Broker(
        open_orders=[{"order_id": "o1"}, {"order_id": "o2"}],
        positions=[],
        fail_on={"o1"},
    )
    report = flatten.flatten_and_cancel(
        "robinhood", broker.submit, broker.read_positions, broker.read_open_orders
    )
    # o1 failed once and was NOT retried; o2 still cancelled.
    assert [r for r in broker.calls if r[1].get("order_id") == "o1"] == [
        ("cancel", {"action": "cancel", "order_id": "o1"})
    ]
    assert report["cancelled_order_ids"] == ["o2"]
    assert report["errors"] == [
        {"phase": "cancel", "order_id": "o1", "error": "broker rejected o1"}
    ]


def test_errored_flatten_is_not_retried(live_runtime: Path) -> None:
    broker = _Broker(
        open_orders=[],
        positions=[{"symbol": "NVDA", "qty": 3}, {"symbol": "AAPL", "qty": 1}],
        fail_on={"NVDA"},
    )
    report = flatten.flatten_and_cancel(
        "robinhood",
        broker.submit,
        broker.read_positions,
        broker.read_open_orders,
        allow_flatten=True,
    )
    nvda_calls = [r for r in broker.calls if r[1].get("symbol") == "NVDA"]
    assert len(nvda_calls) == 1  # errored once, not retried
    assert [s["symbol"] for s in report["flatten_orders_submitted"]] == ["AAPL"]
    assert report["errors"] == [
        {"phase": "flatten", "symbol": "NVDA", "error": "broker rejected NVDA"}
    ]


def test_every_action_is_audited(live_runtime: Path) -> None:
    broker = _Broker(
        open_orders=[{"order_id": "o1"}],
        positions=[{"symbol": "NVDA", "qty": 2}],
        fail_on={"o1"},
    )
    flatten.flatten_and_cancel(
        "robinhood",
        broker.submit,
        broker.read_positions,
        broker.read_open_orders,
        allow_flatten=True,
    )
    records = _read_ledger()
    # One audit per broker call: failed cancel (rejected) + accepted flatten.
    kinds = sorted(r["kind"] for r in records)
    assert kinds == ["order_placed", "order_rejected"]
    rejected = next(r for r in records if r["kind"] == "order_rejected")
    assert rejected["remote_tool"] == "cancel_order"
    assert rejected["outcome"] == "error"
    assert rejected["error"] == "broker rejected o1"
    placed = next(r for r in records if r["kind"] == "order_placed")
    assert placed["remote_tool"] == "place_order"
    assert placed["outcome"] == "accepted"
    assert placed["server"] == "robinhood"


def test_read_failure_recorded_not_raised(live_runtime: Path) -> None:
    def boom_orders() -> list[dict[str, Any]]:
        raise RuntimeError("read failed")

    broker = _Broker(open_orders=[], positions=[])
    report = flatten.flatten_and_cancel(
        "robinhood", broker.submit, broker.read_positions, boom_orders
    )
    assert {"phase": "read_open_orders", "error": "read failed"} in report["errors"]


def test_mandate_flatten_flag_honored(
    live_runtime: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # When a (future) mandate exposes a truthy flatten_on_halt, flatten runs
    # without an explicit allow_flatten override.
    class _Mandate:
        flatten_on_halt = True

    monkeypatch.setattr(flatten, "load_mandate", lambda broker: _Mandate())
    broker = _Broker(open_orders=[], positions=[{"symbol": "NVDA", "qty": 1}])
    report = flatten.flatten_and_cancel(
        "robinhood", broker.submit, broker.read_positions, broker.read_open_orders
    )
    assert [s["symbol"] for s in report["flatten_orders_submitted"]] == ["NVDA"]
    assert report["flatten_skipped_reason"] is None
