"""Focused tests for Shadow Account signal scanning."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.shadow_account.models import ShadowProfile, ShadowRule
from src.shadow_account.scanner import scan_today_signals


def _profile(entry_condition: dict[str, object] | None = None) -> ShadowProfile:
    """Build a minimal ShadowProfile for scanner tests."""
    rule = ShadowRule(
        rule_id="R1",
        human_text="momentum entry",
        entry_condition=entry_condition or {"market": "us"},
        exit_condition={},
        holding_days_range=(3, 7),
        support_count=5,
        coverage_rate=0.5,
        sample_trades=("AAPL@2026-01-01",),
    )
    return ShadowProfile(
        shadow_id="shadow_test",
        created_at="2026-01-01T00:00:00Z",
        journal_hash="hash",
        source_market="us",
        profitable_roundtrips=5,
        total_roundtrips=8,
        date_range=("2026-01-01", "2026-02-01"),
        profile_text="test profile",
        rules=(rule,),
        preferred_markets=("us",),
        typical_holding_days=(5.0, 7.0),
    )


def _bars(closes: list[float], volumes: list[float] | None = None) -> pd.DataFrame:
    """Create a dated OHLCV frame ending on the scanner target date."""
    index = pd.date_range("2026-04-01", periods=len(closes), freq="D")
    data: dict[str, list[float]] = {
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
    }
    if volumes is not None:
        data["volume"] = volumes
    return pd.DataFrame(data, index=index)


@pytest.mark.unit
def test_scan_today_signals_matches_price_features() -> None:
    profile = _profile()
    frames = {
        "AAPL": _bars(
            [10, 10.2, 10.4, 10.5, 10.7, 11.4],
            [100, 100, 100, 100, 100, 180],
        ),
    }

    matches = scan_today_signals(profile, target_date=date(2026, 4, 6), price_frames=frames)

    assert matches == [
        {
            "symbol": "AAPL",
            "market": "us",
            "rule_id": "R1",
            "reason": "R1 price features matched (hold 3-7d)",
        }
    ]


@pytest.mark.unit
def test_scan_today_signals_returns_no_match_when_features_fail() -> None:
    profile = _profile()
    frames = {
        "AAPL": _bars(
            [11.5, 11.2, 11.0, 10.9, 10.7, 10.5],
            [180, 160, 150, 140, 130, 100],
        ),
    }

    assert scan_today_signals(profile, target_date="2026-04-06", price_frames=frames) == []


@pytest.mark.unit
def test_scan_today_signals_skips_missing_and_empty_data() -> None:
    profile = _profile()
    frames = {"AAPL": pd.DataFrame(), "MSFT": pd.DataFrame({"open": [1, 2]})}

    assert scan_today_signals(profile, target_date="2026-04-06", price_frames=frames) == []


@pytest.mark.unit
def test_scan_today_signals_keeps_backwards_compatible_call_signature() -> None:
    profile = _profile()

    assert scan_today_signals(profile, target_date="2026-04-06", per_market=1) == []


@pytest.mark.unit
def test_scan_today_signals_respects_per_market_cap() -> None:
    profile = _profile({"market": "us", "prior_5d_return": (">", 0.05)})
    frame = _bars(
        [10, 10.2, 10.4, 10.5, 10.7, 11.4],
        [100, 100, 100, 100, 100, 180],
    )
    frames = {symbol: frame for symbol in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]}

    matches = scan_today_signals(
        profile,
        target_date="2026-04-06",
        per_market=2,
        price_frames=frames,
    )

    assert [match["symbol"] for match in matches] == ["AAPL", "MSFT"]


def _ramp(n: int, start: float, step: float) -> list[float]:
    """Monotonic close series of length n — drives RSI toward an extreme."""
    return [start + step * i for i in range(n)]


@pytest.mark.unit
def test_scan_today_signals_matches_rsi_range_condition() -> None:
    """An RSI ``{min,max}`` bound must be honored by the scanner (PR #314).

    Before the fix, ``entry_rsi14`` mapped to no feature and the bound was
    silently dropped; a steady uptrend pins RSI near 100 and should match a
    wide [50, 100] band.
    """
    profile = _profile({"market": "us", "entry_rsi14": {"min": 50.0, "max": 100.0}})
    closes = _ramp(20, 10.0, 0.2)  # >= 14 bars so RSI is defined
    target = pd.Timestamp("2026-04-01") + pd.Timedelta(days=len(closes) - 1)
    frames = {"AAPL": _bars(closes)}

    matches = scan_today_signals(profile, target_date=target.date(), price_frames=frames)

    assert [m["symbol"] for m in matches] == ["AAPL"]


@pytest.mark.unit
def test_scan_today_signals_rejects_out_of_band_rsi() -> None:
    """A steady uptrend (RSI ~100) must fail a low-RSI [0, 30] band."""
    profile = _profile({"market": "us", "entry_rsi14": {"min": 0.0, "max": 30.0}})
    closes = _ramp(20, 10.0, 0.2)
    target = pd.Timestamp("2026-04-01") + pd.Timedelta(days=len(closes) - 1)
    frames = {"AAPL": _bars(closes)}

    assert scan_today_signals(profile, target_date=target.date(), price_frames=frames) == []


@pytest.mark.unit
def test_scan_today_signals_honors_prior_return_dict_band() -> None:
    """``prior_5d_return`` as a ``{min,max}`` dict must range-check momentum.

    Before the fix the dict reached ``_to_float`` and returned ``None`` → the
    bound was skipped. The 5-day return here is 11.4/10 - 1 = 0.14, inside the
    band; a too-high floor must reject it.
    """
    closes = [10, 10.2, 10.4, 10.5, 10.7, 11.4]
    frames = {"AAPL": _bars(closes)}

    inside = _profile({"market": "us", "prior_5d_return": {"min": 0.10, "max": 0.20}})
    assert [m["symbol"] for m in scan_today_signals(
        inside, target_date="2026-04-06", price_frames=frames)] == ["AAPL"]

    outside = _profile({"market": "us", "prior_5d_return": {"min": 0.50, "max": 1.0}})
    assert scan_today_signals(outside, target_date="2026-04-06", price_frames=frames) == []


@pytest.mark.unit
def test_scan_today_signals_no_match_when_rsi_history_insufficient() -> None:
    """Too few bars to compute RSI → the RSI-bearing rule cannot match."""
    profile = _profile({"market": "us", "entry_rsi14": {"min": 0.0, "max": 100.0}})
    frames = {"AAPL": _bars(_ramp(6, 10.0, 0.2))}  # < 14 bars, RSI undefined

    assert scan_today_signals(profile, target_date="2026-04-06", price_frames=frames) == []

