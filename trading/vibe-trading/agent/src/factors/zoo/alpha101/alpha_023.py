
# ============================================================
# 中文名称: Kakushadze Alpha #23
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第23号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #23.

Formula (paper appendix): ((sum(high,20)/20) < high) ? (-1*delta(high,2)) : 0
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 23.
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

ALPHA_ID = "alpha101_023"

__alpha_meta__ = {
    'id': 'alpha101_023',
    'nickname': 'Kakushadze Alpha #23',
    'theme': ['momentum'],
    'formula_latex': '((sum(high,20)/20) < high) ? (-1*delta(high,2)) : 0',
    'columns_required': ['high', 'close'],
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
    high = panel["high"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    where_ternary = _where_ternary
    mh = rolling_sum(high, 20) / 20.0
    out = where_ternary(mh < high, -1.0 * delta(high, 2), 0.0 * close)
    return out
