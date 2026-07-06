
# ============================================================
# 中文名称: Alpha #7 - VWAP动量
# 简要说明: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * volume))，条件量价动量。
# 典型用途: 放量条件下跟踪趋势方向，缩量条件下做空成交量本身。
# ============================================================
"""Kakushadze Alpha #7.

Formula (paper appendix): (adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 7.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
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
)

ALPHA_ID = "alpha101_007"

__alpha_meta__ = {
    'id': 'alpha101_007',
    'nickname': 'Kakushadze Alpha #7',
    'theme': ['momentum', 'volume'],
    'formula_latex': '(adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1)',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 67,
    'notes': '',
}


def _make_one(ref: pd.DataFrame) -> pd.DataFrame:
    """A DataFrame of 1.0 with the same shape/index/columns as ``ref``."""
    return pd.DataFrame(1.0, index=ref.index, columns=ref.columns)


def _where_ternary(cond, a, b):
    """Vectorised ternary `(cond ? a : b)` returning a DataFrame.

    ``cond`` is a boolean DataFrame; ``a`` / ``b`` may be DataFrame or scalar.
    """
    if isinstance(a, (int, float)):
        a_arr = np.full_like(cond.to_numpy(dtype=np.float64), float(a))
    else:
        a_arr = a.to_numpy(dtype=np.float64, na_value=np.nan)
    if isinstance(b, (int, float)):
        b_arr = np.full_like(cond.to_numpy(dtype=np.float64), float(b))
    else:
        b_arr = b.to_numpy(dtype=np.float64, na_value=np.nan)
    cond_arr = cond.to_numpy(dtype=bool, na_value=False) if hasattr(cond, "to_numpy") else np.asarray(cond, dtype=bool)
    out = np.where(cond_arr, a_arr, b_arr)
    out = np.where(np.isfinite(out), out, np.nan)
    idx = cond.index if hasattr(cond, "index") else a.index
    cols = cond.columns if hasattr(cond, "columns") else a.columns
    return pd.DataFrame(out, index=idx, columns=cols)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    make_one = _make_one
    where_ternary = _where_ternary
    d7 = delta(close, 7)
    expr = (-1.0 * ts_rank(d7.abs(), 60)) * np.sign(d7)
    out = where_ternary(adv20 < volume, expr, -1.0 * make_one(close))
    return out
