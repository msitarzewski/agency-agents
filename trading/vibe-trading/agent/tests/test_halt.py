"""Tests for the live-trading kill switch (src/live/halt.py, SPEC Consent §4).

The kill switch is a pure-filesystem sentinel — independent of any LLM/agent
state — so these tests exercise it purely through the filesystem.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.live import halt
from src.live import paths


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live runtime root at an isolated tmp dir."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def test_not_halted_when_no_sentinel(live_runtime: Path) -> None:
    assert halt.halt_flag_set() is False
    assert halt.halt_flag_set("robinhood") is False
    assert halt.read_halt() is None


def test_global_trip_and_clear(live_runtime: Path) -> None:
    path = halt.trip_halt(by="cli", reason="user said stop")
    assert path.exists()
    assert halt.halt_flag_set() is True
    # Global sentinel halts every broker regardless of per-broker state.
    assert halt.halt_flag_set("robinhood") is True
    assert halt.halt_flag_set("anything") is True

    meta = halt.read_halt()
    assert meta is not None
    assert meta["by"] == "cli"
    assert meta["reason"] == "user said stop"
    assert "tripped_at" in meta

    assert halt.clear_halt() is True
    assert halt.halt_flag_set() is False
    # Clearing an already-clear switch is a no-op returning False.
    assert halt.clear_halt() is False


def test_per_broker_trip_is_scoped(live_runtime: Path) -> None:
    halt.trip_halt(by="frontend", reason="halt one broker", broker="robinhood")
    assert halt.halt_flag_set("robinhood") is True
    # A different broker is unaffected, and the global check stays clear.
    assert halt.halt_flag_set("alpaca") is False
    assert halt.halt_flag_set() is False
    # Clearing the broker sentinel does not require touching the global one.
    assert halt.clear_halt(broker="robinhood") is True
    assert halt.halt_flag_set("robinhood") is False


def test_global_wins_over_broker(live_runtime: Path) -> None:
    halt.trip_halt(by="cli", reason="broker only", broker="robinhood")
    halt.trip_halt(by="cli", reason="global")
    # Clearing the global still leaves the broker sentinel in effect.
    halt.clear_halt()
    assert halt.halt_flag_set("robinhood") is True


def test_existence_is_authoritative_even_if_malformed(live_runtime: Path) -> None:
    # A user/watchdog touching the file with junk still counts as halted;
    # only the attribution metadata is unreadable.
    path = halt.halt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json", encoding="utf-8")
    assert halt.halt_flag_set() is True
    assert halt.read_halt() == {}


def test_bare_touch_trips_without_metadata(live_runtime: Path) -> None:
    path = halt.halt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    assert halt.halt_flag_set() is True
    assert halt.read_halt() == {}


def test_invalid_broker_fails_closed(live_runtime: Path) -> None:
    # An unresolvable broker key (path traversal) can never be safely traded.
    assert halt.halt_flag_set("../evil") is True


def test_trip_is_idempotent_latest_wins(live_runtime: Path) -> None:
    halt.trip_halt(by="cli", reason="first")
    halt.trip_halt(by="frontend", reason="second")
    meta = halt.read_halt()
    assert meta is not None
    assert meta["by"] == "frontend"
    assert meta["reason"] == "second"


# --- Preemptive halt action hook (SPEC §7.5 component 6) ------------------


@pytest.fixture(autouse=True)
def _clear_halt_actions() -> object:
    """Isolate the module-level action registry between tests."""
    halt._HALT_ACTIONS.clear()
    yield
    halt._HALT_ACTIONS.clear()


def test_on_halt_action_noop_when_unregistered(live_runtime: Path) -> None:
    # No action registered → no-op returning None (cooperative gate still blocks).
    assert halt.on_halt_action("robinhood") is None


def test_register_and_run_halt_action(live_runtime: Path) -> None:
    seen: list[str] = []
    halt.register_halt_action(lambda broker: seen.append(broker) or "swept")
    assert halt.on_halt_action("robinhood") == "swept"
    assert seen == ["robinhood"]


def test_broker_action_overrides_global(live_runtime: Path) -> None:
    halt.register_halt_action(lambda broker: "global")
    halt.register_halt_action(lambda broker: "rh", broker="robinhood")
    assert halt.on_halt_action("robinhood") == "rh"
    assert halt.on_halt_action("alpaca") == "global"


def test_unregister_halt_action(live_runtime: Path) -> None:
    halt.register_halt_action(lambda broker: "x", broker="robinhood")
    assert halt.unregister_halt_action(broker="robinhood") is True
    assert halt.unregister_halt_action(broker="robinhood") is False
    assert halt.on_halt_action("robinhood") is None


def test_register_is_idempotent_latest_wins(live_runtime: Path) -> None:
    halt.register_halt_action(lambda broker: "first", broker="robinhood")
    halt.register_halt_action(lambda broker: "second", broker="robinhood")
    assert halt.on_halt_action("robinhood") == "second"


def test_action_exception_propagates(live_runtime: Path) -> None:
    def boom(broker: str) -> object:
        raise RuntimeError("flatten failed")

    halt.register_halt_action(boom, broker="robinhood")
    with pytest.raises(RuntimeError, match="flatten failed"):
        halt.on_halt_action("robinhood")
