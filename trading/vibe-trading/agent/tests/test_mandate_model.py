"""Mandate model + read-only store: round-trip, absent→None, expiry parse."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import src.live.paths as paths
from src.live.mandate.model import (
    MANDATE_SCHEMA_VERSION,
    AssetClass,
    ConsentMeta,
    HardCaps,
    InstrumentType,
    Mandate,
    UniverseConstraint,
)
from src.live.mandate.store import load_mandate


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live root at a tmp dir so tests never touch the real store."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def _sample_mandate(expires_at: str, *, flatten_on_halt: bool = False) -> Mandate:
    return Mandate(
        schema_version=MANDATE_SCHEMA_VERSION,
        flatten_on_halt=flatten_on_halt,
        hard_caps=HardCaps(
            account_funding_usd=5000.0,
            max_order_notional_usd=750.0,
            max_total_exposure_usd=5000.0,
            max_leverage=1.0,
            allowed_instruments=(InstrumentType.EQUITY, InstrumentType.ETF),
            max_trades_per_day=5,
        ),
        universe=UniverseConstraint(
            asset_classes=(AssetClass.US_EQUITY, AssetClass.US_ETF),
            min_market_cap_usd=2_000_000_000.0,
            min_avg_daily_volume_usd=None,
            exclude_symbols=("TSLA", "GME"),
        ),
        consent=ConsentMeta(
            created_at="2026-05-29T14:00:00Z",
            consent_token_sha256="a" * 64,
            broker="robinhood",
            account_ref="rh_acct_opaque",
            expires_at=expires_at,
        ),
    )


def _write_mandate(broker_path: Path, mandate: Mandate) -> None:
    broker_path.mkdir(parents=True, exist_ok=True)
    caps = mandate.hard_caps
    universe = mandate.universe
    consent = mandate.consent
    payload = {
        "schema_version": mandate.schema_version,
        "flatten_on_halt": mandate.flatten_on_halt,
        "hard_caps": {
            "account_funding_usd": caps.account_funding_usd,
            "max_order_notional_usd": caps.max_order_notional_usd,
            "max_total_exposure_usd": caps.max_total_exposure_usd,
            "max_leverage": caps.max_leverage,
            "allowed_instruments": [i.value for i in caps.allowed_instruments],
            "max_trades_per_day": caps.max_trades_per_day,
        },
        "universe": {
            "asset_classes": [a.value for a in universe.asset_classes],
            "min_market_cap_usd": universe.min_market_cap_usd,
            "min_avg_daily_volume_usd": universe.min_avg_daily_volume_usd,
            "exclude_symbols": list(universe.exclude_symbols),
        },
        "consent": {
            "created_at": consent.created_at,
            "consent_token_sha256": consent.consent_token_sha256,
            "broker": consent.broker,
            "account_ref": consent.account_ref,
            "expires_at": consent.expires_at,
        },
    }
    (broker_path / "mandate.json").write_text(json.dumps(payload), encoding="utf-8")


def test_load_mandate_round_trip(live_runtime: Path) -> None:
    """A written mandate loads back into an equal frozen object."""
    expires = "2026-06-28T14:00:00Z"
    original = _sample_mandate(expires)
    from src.live.paths import broker_dir

    _write_mandate(broker_dir("robinhood"), original)
    loaded = load_mandate("robinhood")

    assert loaded == original
    # Frozen dataclass — enums survive the round-trip.
    assert loaded.hard_caps.allowed_instruments == (
        InstrumentType.EQUITY,
        InstrumentType.ETF,
    )
    assert loaded.universe.asset_classes == (AssetClass.US_EQUITY, AssetClass.US_ETF)
    assert loaded.universe.min_avg_daily_volume_usd is None


def test_flatten_on_halt_round_trips(live_runtime: Path) -> None:
    """A mandate written with flatten_on_halt=True loads back True (M3)."""
    from src.live.paths import broker_dir

    _write_mandate(broker_dir("robinhood"), _sample_mandate("2026-06-28T14:00:00Z", flatten_on_halt=True))
    loaded = load_mandate("robinhood")
    assert loaded is not None
    assert loaded.flatten_on_halt is True


def test_flatten_on_halt_absent_defaults_false(live_runtime: Path) -> None:
    """An OLD mandate.json lacking flatten_on_halt loads as False (cancel-only).

    Backward compatibility: the field is optional with a safe default, so a
    mandate written before the field existed must not break the loader and must
    default to cancel-only.
    """
    from src.live.paths import broker_dir

    bdir = broker_dir("robinhood")
    _write_mandate(bdir, _sample_mandate("2026-06-28T14:00:00Z"))
    # Strip the field to simulate a pre-flatten_on_halt mandate.json on disk.
    doc = json.loads((bdir / "mandate.json").read_text(encoding="utf-8"))
    doc.pop("flatten_on_halt", None)
    (bdir / "mandate.json").write_text(json.dumps(doc), encoding="utf-8")

    loaded = load_mandate("robinhood")
    assert loaded is not None
    assert loaded.flatten_on_halt is False


def test_load_mandate_absent_returns_none(live_runtime: Path) -> None:
    """No file on disk → None (fail-closed, gate denies)."""
    assert load_mandate("robinhood") is None


def test_load_mandate_malformed_json_returns_none(live_runtime: Path) -> None:
    """Unparseable JSON → None rather than an exception."""
    from src.live.paths import broker_dir

    bdir = broker_dir("robinhood")
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "mandate.json").write_text("{not json", encoding="utf-8")
    assert load_mandate("robinhood") is None


def test_load_mandate_missing_field_returns_none(live_runtime: Path) -> None:
    """A structurally invalid record (missing section) → None (fail-closed)."""
    from src.live.paths import broker_dir

    bdir = broker_dir("robinhood")
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "mandate.json").write_text(
        json.dumps({"schema_version": MANDATE_SCHEMA_VERSION}), encoding="utf-8"
    )
    assert load_mandate("robinhood") is None


def test_expires_at_parses_as_utc_datetime(live_runtime: Path) -> None:
    """expires_at round-trips as an ISO-8601 UTC timestamp the gate can parse."""
    created = datetime(2026, 5, 29, 14, 0, 0, tzinfo=timezone.utc)
    expires_dt = created + timedelta(days=30)
    expires = expires_dt.isoformat().replace("+00:00", "Z")
    from src.live.paths import broker_dir

    _write_mandate(broker_dir("robinhood"), _sample_mandate(expires))
    loaded = load_mandate("robinhood")

    assert loaded is not None
    parsed = datetime.fromisoformat(loaded.consent.expires_at.replace("Z", "+00:00"))
    assert parsed == expires_dt
    assert parsed - created == timedelta(days=30)


def test_broker_dir_rejects_path_traversal() -> None:
    """A broker key is never a path — separators / .. are rejected."""
    from src.live.paths import broker_dir

    for bad in ("../escape", "rob/inhood", "a\\b", ".."):
        with pytest.raises(ValueError):
            broker_dir(bad)
    with pytest.raises(ValueError):
        broker_dir("  ")
