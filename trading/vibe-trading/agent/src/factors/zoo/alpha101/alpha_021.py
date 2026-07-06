
# ============================================================
# 中文名称: Kakushadze Alpha #21
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第21号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #21.

Formula (paper appendix): complex piecewise; see paper
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 21.
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

ALPHA_ID = "alpha101_021"

__alpha_meta__ = {
    'id': 'alpha101_021',
    'nickname': 'Kakushadze Alpha #21',
    'theme': ['momentum', 'volatility'],
    'formula_latex': 'complex piecewise; see paper',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 20,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


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
    rolling_sum = _rolling_sum
    make_one = _make_one
    where_ternary = _where_ternary
    m8 = rolling_sum(close, 8) / 8.0
    s8 = ts_std(close, 8)
    m2 = rolling_sum(close, 2) / 2.0
    v_adv = safe_div(volume, adv20)
    cond_a = (m8 + s8) < m2
    cond_b = m2 < (m8 - s8)
    cond_c = (v_adv >= 1.0)
    one = make_one(close)
    out = where_ternary(cond_a, -1.0 * one, where_ternary(cond_b, one, where_ternary(cond_c, one, -1.0 * one)))
    return out
