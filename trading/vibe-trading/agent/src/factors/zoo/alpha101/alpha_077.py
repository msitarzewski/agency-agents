
# ============================================================
# 中文名称: Kakushadze Alpha #77
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第77号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #77.

Formula (paper appendix): min(rank(decay_linear((high+low)/2 + high - (vwap+high), 20)), rank(decay_linear(correlation((high+low)/2, adv40, 3), 6)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 77.
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

ALPHA_ID = "alpha101_077"

__alpha_meta__ = {
    'id': 'alpha101_077',
    'nickname': 'Kakushadze Alpha #77',
    'theme': ['volume'],
    'formula_latex': 'min(rank(decay_linear((high+low)/2 + high - (vwap+high), 20)), rank(decay_linear(correlation((high+low)/2, adv40, 3), 6)))',
    'columns_required': ['high', 'low', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 47,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv40 = ts_mean(volume, 40)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    a = rank(decay_linear(((high + low) / 2.0) + high - (vwap + high), 20))
    b = rank(decay_linear(ts_corr((high + low) / 2.0, adv40, 3), 6))
    arr_a = a.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = b.to_numpy(dtype=np.float64, na_value=np.nan)
    out = pd.DataFrame(np.fmin(arr_a, arr_b), index=close.index, columns=close.columns)
    return out
