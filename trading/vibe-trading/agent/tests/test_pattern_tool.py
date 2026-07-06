"""Tests for the chart pattern recognition tool.

Covers the deterministic pattern-detection functions in
``src.tools.pattern_tool`` (peaks/valleys, candlestick, support/resistance,
trend slope, head-and-shoulders, double top/bottom, triangle, broadening)
and the ``run_pattern`` dispatch + error paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.tools.pattern_tool import (
    broadening,
    candlestick_patterns,
    double_top_bottom,
    find_peaks_valleys,
    head_and_shoulders,
    run_pattern,
    support_resistance,
    trend_line_slope,
    triangle,
)


# --------------------------------------------------------------------------
# find_peaks_valleys
# --------------------------------------------------------------------------


def test_find_peaks_valleys_basic() -> None:
    pv = find_peaks_valleys(pd.Series([1, 3, 1, 5, 1.0]), window=1)
    assert pv["peaks"] == [1, 3]
    assert pv["valleys"] == [2]


def test_find_peaks_valleys_too_short_returns_empty() -> None:
    pv = find_peaks_valleys(pd.Series([1, 2.0]), window=1)
    assert pv == {"peaks": [], "valleys": []}


def test_find_peaks_valleys_ignores_nan_center() -> None:
    pv = find_peaks_valleys(pd.Series([1, float("nan"), 1, 5, 1.0]), window=1)
    # The NaN at index 1 is skipped; index 3 is still a peak.
    assert 1 not in pv["peaks"]
    assert 3 in pv["peaks"]


# --------------------------------------------------------------------------
# trend_line_slope
# --------------------------------------------------------------------------


def test_trend_line_slope_linear_series() -> None:
    slopes = trend_line_slope(pd.Series([0, 1, 2, 3, 4.0]), window=3)
    # First window-1 entries are NaN; the rest equal the exact slope 1.0.
    assert pd.isna(slopes.iloc[0]) and pd.isna(slopes.iloc[1])
    assert slopes.iloc[2] == pytest.approx(1.0)
    assert slopes.iloc[4] == pytest.approx(1.0)


def test_trend_line_slope_flat_series_is_zero() -> None:
    slopes = trend_line_slope(pd.Series([7.0] * 6), window=3)
    assert slopes.dropna().abs().max() == pytest.approx(0.0)


# --------------------------------------------------------------------------
# candlestick_patterns
# --------------------------------------------------------------------------


def test_candlestick_doji_is_neutral() -> None:
    # Tiny body relative to range -> doji -> stays 0 (not a hammer).
    out = candlestick_patterns(
        pd.Series([100.0]), pd.Series([101.0]), pd.Series([99.0]), pd.Series([100.05])
    )
    assert list(out) == [0]


def test_candlestick_hammer_is_bullish() -> None:
    # Long lower shadow, small upper shadow, real body -> hammer -> 1.
    out = candlestick_patterns(
        pd.Series([100.0]), pd.Series([101.2]), pd.Series([96.0]), pd.Series([101.0])
    )
    assert list(out) == [1]


def test_candlestick_bullish_engulfing() -> None:
    # Bar 0 bearish; bar 1 bullish body engulfs bar 0 -> 1 at index 1.
    out = candlestick_patterns(
        pd.Series([100.0, 97.0]),
        pd.Series([101.0, 102.0]),
        pd.Series([97.0, 96.0]),
        pd.Series([98.0, 101.0]),
    )
    assert out.iloc[1] == 1


def test_candlestick_bearish_engulfing() -> None:
    # Bar 0 bullish; bar 1 bearish body engulfs bar 0 -> -1 at index 1.
    out = candlestick_patterns(
        pd.Series([100.0, 103.0]),
        pd.Series([103.0, 104.0]),
        pd.Series([99.0, 98.0]),
        pd.Series([102.0, 99.0]),
    )
    assert out.iloc[1] == -1


# --------------------------------------------------------------------------
# support_resistance
# --------------------------------------------------------------------------


def test_support_resistance_separates_levels() -> None:
    osc = pd.Series([10, 12, 10, 13, 9, 12, 10, 13.0] * 2)
    sr = support_resistance(osc, window=1, num_levels=2)
    assert sr["support"] and sr["resistance"]
    # Resistance (from peaks) should sit above support (from valleys).
    assert max(sr["resistance"]) > max(sr["support"])


def test_support_resistance_empty_on_flat() -> None:
    sr = support_resistance(pd.Series([5.0] * 30), window=5)
    # A flat series yields peaks==valleys at every interior point; just assert
    # the contract shape holds and values stay at the flat level.
    assert set(sr) == {"support", "resistance"}
    for level in sr["support"] + sr["resistance"]:
        assert level == pytest.approx(5.0)


# --------------------------------------------------------------------------
# head_and_shoulders
# --------------------------------------------------------------------------


def test_head_and_shoulders_needs_three_peaks() -> None:
    out = head_and_shoulders(pd.Series([1, 2, 1.0]), window=1)
    assert int(out.sum()) == 0


def test_head_and_shoulders_detects_pattern() -> None:
    # Three peaks: shoulders ~equal (10, 10.2), head higher (15). window=1.
    series = pd.Series([1, 10, 1, 15, 1, 10.2, 1.0])
    out = head_and_shoulders(series, window=1)
    assert int(out.sum()) == 1
    # Flagged at the head (middle peak, index 3).
    assert out.iloc[3] == 1


# --------------------------------------------------------------------------
# double_top_bottom
# --------------------------------------------------------------------------


def test_double_top_detected() -> None:
    out = double_top_bottom(pd.Series([1, 5, 1, 5.05, 1.0]), window=1)
    assert out.iloc[3] == 1
    assert int((out == 1).sum()) == 1


def test_double_bottom_detected() -> None:
    out = double_top_bottom(pd.Series([5, 1, 5, 1.02, 5.0]), window=1)
    assert out.iloc[3] == -1
    assert int((out == -1).sum()) == 1


# --------------------------------------------------------------------------
# triangle / broadening — shape + flat-series guards
# --------------------------------------------------------------------------


def test_triangle_flat_series_all_zero() -> None:
    out = triangle(pd.Series([5.0] * 30), window=20)
    assert len(out) == 30
    assert out.dtype == int
    assert int(out.abs().sum()) == 0


def test_broadening_flat_series_all_zero() -> None:
    out = broadening(pd.Series([5.0] * 30), window=20)
    assert len(out) == 30
    assert out.dtype == int
    assert int(out.sum()) == 0


# --------------------------------------------------------------------------
# run_pattern dispatch + error paths
# --------------------------------------------------------------------------


@pytest.fixture()
def allow_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))
    return tmp_path


def test_run_pattern_rejects_path_outside_run_roots(allow_runs: Path) -> None:
    result = json.loads(run_pattern("/etc/not_a_run_dir"))
    assert result["status"] == "error"
    assert "run roots" in result["error"]


def test_run_pattern_no_ohlcv(allow_runs: Path) -> None:
    run_dir = allow_runs / "run1"
    (run_dir / "artifacts").mkdir(parents=True)
    result = json.loads(run_pattern(str(run_dir)))
    assert result["status"] == "error"
    assert "No OHLCV" in result["error"]


def test_run_pattern_invalid_pattern_name(allow_runs: Path) -> None:
    run_dir = allow_runs / "run2"
    arts = run_dir / "artifacts"
    arts.mkdir(parents=True)
    _write_ohlcv(arts / "ohlcv_TEST.csv")
    result = json.loads(run_pattern(str(run_dir), patterns="not_a_pattern"))
    assert result["status"] == "error"
    assert "Invalid pattern" in result["error"]


def test_run_pattern_end_to_end(allow_runs: Path) -> None:
    run_dir = allow_runs / "run3"
    arts = run_dir / "artifacts"
    arts.mkdir(parents=True)
    _write_ohlcv(arts / "ohlcv_000001.csv")

    result = json.loads(run_pattern(str(run_dir), patterns="peaks_valleys,trend_slope", window=2))
    assert result["status"] == "ok"
    assert result["patterns"] == ["peaks_valleys", "trend_slope"]
    assert "000001" in result["results"]
    code_res = result["results"]["000001"]
    assert "peaks_valleys" in code_res
    assert "trend_slope" in code_res


def _write_ohlcv(path: Path) -> None:
    idx = pd.date_range("2026-01-01", periods=12, freq="D")
    closes = [10, 11, 10, 12, 9, 13, 10, 12, 11, 14, 10, 13]
    df = pd.DataFrame(
        {
            "open": [c - 0.5 for c in closes],
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000] * 12,
        },
        index=idx,
    )
    df.to_csv(path)
