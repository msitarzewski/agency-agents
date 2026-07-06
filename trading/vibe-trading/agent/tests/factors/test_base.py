"""Operator unit tests — NaN propagation, divide-by-zero, warmup, lookahead ban."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.factors.base import (
    Alpha,
    AlphaCompute,
    Market,
    decay_linear,
    delta,
    rank,
    safe_div,
    scale,
    signed_power,
    ts_argmax,
    ts_argmin,
    ts_corr,
    ts_cov,
    ts_max,
    ts_mean,
    ts_min,
    ts_rank,
    ts_std,
    vwap,
)


def _frame(rows: list[list[float]], dates: int | None = None) -> pd.DataFrame:
    n = dates if dates is not None else len(rows)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame(rows, index=idx, columns=list("ABCD")[: len(rows[0])])


# ---------------- rank / scale ----------------


def test_rank_pct_per_row() -> None:
    df = _frame([[1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]])
    r = rank(df)
    assert pytest.approx(r.iloc[0].tolist()) == [0.25, 0.5, 0.75, 1.0]
    assert pytest.approx(r.iloc[1].tolist()) == [1.0, 0.75, 0.5, 0.25]


def test_rank_preserves_nan_row() -> None:
    df = _frame([[np.nan, np.nan, np.nan, np.nan]])
    assert rank(df).isna().all().all()


def test_rank_partial_nan_row() -> None:
    df = _frame([[1.0, np.nan, 3.0, np.nan]])
    r = rank(df)
    assert np.isnan(r.iloc[0, 1])
    assert np.isnan(r.iloc[0, 3])
    assert r.iloc[0, 0] < r.iloc[0, 2]


def test_scale_l1_normalises() -> None:
    df = _frame([[1.0, -2.0, 3.0, -4.0]])
    s = scale(df, a=1.0)
    assert pytest.approx(s.abs().sum(axis=1).iloc[0]) == 1.0


def test_scale_zero_row_returns_nan() -> None:
    df = _frame([[0.0, 0.0, 0.0, 0.0]])
    assert scale(df).isna().all().all()


# ---------------- ts_* warmup + edges ----------------


def test_ts_mean_warmup_is_nan() -> None:
    df = _frame([[i, i] for i in range(5)])
    out = ts_mean(df, 3)
    assert out.iloc[:2].isna().all().all()
    assert pytest.approx(out.iloc[2, 0]) == 1.0
    assert pytest.approx(out.iloc[4, 0]) == 3.0


def test_ts_corr_constant_window_is_nan() -> None:
    x = _frame([[1.0, 1.0]] * 5)
    y = _frame([[float(i), float(i)] for i in range(5)])
    out = ts_corr(x, y, 3)
    assert out.iloc[2:].isna().all().all()


def test_ts_std_warmup_window() -> None:
    df = _frame([[1.0], [2.0], [3.0], [4.0], [5.0]])
    out = ts_std(df, 3)
    assert out.iloc[:2].isna().all().all()
    assert pytest.approx(out.iloc[2, 0]) == 1.0  # std of [1,2,3]


def test_ts_rank_pct_within_window() -> None:
    df = _frame([[1.0], [3.0], [2.0], [4.0]])
    out = ts_rank(df, 3)
    # window [3,2,4]: last=4 is largest → pct rank ≈ 1.0
    assert pytest.approx(out.iloc[3, 0]) == 1.0


def test_ts_max_min_argmax_argmin() -> None:
    df = _frame([[1.0], [5.0], [3.0], [2.0]])
    assert pytest.approx(ts_max(df, 3).iloc[3, 0]) == 5.0
    assert pytest.approx(ts_min(df, 3).iloc[3, 0]) == 2.0
    # window [5,3,2]: argmax=0, argmin=2
    assert pytest.approx(ts_argmax(df, 3).iloc[3, 0]) == 0.0
    assert pytest.approx(ts_argmin(df, 3).iloc[3, 0]) == 2.0


def test_ts_cov_warmup() -> None:
    x = _frame([[float(i)] for i in range(5)])
    y = _frame([[float(i) * 2] for i in range(5)])
    out = ts_cov(x, y, 3)
    assert out.iloc[:2].isna().all().all()
    assert out.iloc[2, 0] > 0


# ---------------- delta lookahead ban ----------------


def test_delta_d_zero_raises() -> None:
    df = _frame([[1.0]])
    with pytest.raises(ValueError, match="delta lag"):
        delta(df, 0)


def test_delta_negative_raises() -> None:
    df = _frame([[1.0]])
    with pytest.raises(ValueError, match="delta lag"):
        delta(df, -1)


def test_delta_positive_shift() -> None:
    df = _frame([[1.0], [3.0], [6.0], [10.0]])
    out = delta(df, 1)
    assert np.isnan(out.iloc[0, 0])
    assert pytest.approx(out.iloc[1, 0]) == 2.0
    assert pytest.approx(out.iloc[3, 0]) == 4.0


# ---------------- decay_linear ----------------


def test_decay_linear_weights() -> None:
    df = _frame([[1.0], [2.0], [3.0]])
    out = decay_linear(df, 3)
    # weights 3,2,1 / 6 applied to [1,2,3] → (1*3 + 2*2 + 3*1)/6 = 10/6
    assert pytest.approx(out.iloc[2, 0]) == 10.0 / 6.0


def test_decay_linear_warmup() -> None:
    df = _frame([[1.0], [2.0]])
    out = decay_linear(df, 3)
    assert out.isna().all().all()


# ---------------- signed_power ----------------


def test_signed_power_preserves_sign_no_complex() -> None:
    df = _frame([[-4.0, 4.0, 0.0, -1.0]])
    out = signed_power(df, 0.5)
    assert pytest.approx(out.iloc[0].tolist()) == [-2.0, 2.0, 0.0, -1.0]
    assert not np.iscomplexobj(out.to_numpy())


def test_signed_power_p_two() -> None:
    df = _frame([[-3.0, 2.0]])
    out = signed_power(df, 2)
    assert pytest.approx(out.iloc[0].tolist()) == [-9.0, 4.0]


# ---------------- safe_div ----------------


def test_safe_div_zero_denominator_is_nan() -> None:
    a = _frame([[1.0, 2.0]])
    b = _frame([[0.0, 0.0]])
    out = safe_div(a, b)
    assert out.isna().all().all()


def test_safe_div_propagates_nan() -> None:
    a = _frame([[1.0, np.nan]])
    b = _frame([[2.0, 3.0]])
    out = safe_div(a, b)
    assert pytest.approx(out.iloc[0, 0]) == 0.5
    assert np.isnan(out.iloc[0, 1])


# ---------------- vwap ----------------


def test_vwap_us_typical_price() -> None:
    panel = {
        "open": _frame([[10.0]]),
        "high": _frame([[12.0]]),
        "low": _frame([[8.0]]),
        "close": _frame([[11.0]]),
    }
    out = vwap(panel, Market.EQUITY_US)
    assert pytest.approx(out.iloc[0, 0]) == (10 + 12 + 8 + 11) / 4.0


def test_vwap_cn_uses_amount_volume() -> None:
    # Tushare ``amount`` is in 千元 (thousand CNY) and ``volume`` is in 手
    # (100 shares). True VWAP = (amount * 1000 CNY) / (volume * 100 shares).
    panel = {
        "amount": _frame([[10000.0]]),  # 10000 千元 = 10,000,000 CNY
        "volume": _frame([[10.0]]),     # 10 手 = 1000 股
    }
    out = vwap(panel, Market.EQUITY_CN)
    expected = (10000.0 * 1000.0) / (10.0 * 100.0 + 1.0)
    assert pytest.approx(out.iloc[0, 0]) == expected


def test_vwap_prefers_panel_vwap_column() -> None:
    panel = {"vwap": _frame([[42.0]])}
    out = vwap(panel, Market.CRYPTO)
    assert pytest.approx(out.iloc[0, 0]) == 42.0


def test_vwap_us_missing_column_raises() -> None:
    with pytest.raises(KeyError):
        vwap({"open": _frame([[1.0]])}, Market.EQUITY_US)


# ---------------- Alpha dataclass + Protocol ----------------


def test_alpha_dataclass_is_frozen() -> None:
    a = Alpha(id="zoo_001", zoo="zoo", module_path="x.y.z")
    with pytest.raises(Exception):
        a.id = "other"  # type: ignore[misc]


def test_alpha_compute_protocol_runtime_check() -> None:
    def my_alpha(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
        return panel["close"]

    assert isinstance(my_alpha, AlphaCompute)
