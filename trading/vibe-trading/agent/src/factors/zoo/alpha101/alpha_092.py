
# ============================================================
# 中文名称: Kakushadze Alpha #92
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第92号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #92.

Formula (paper appendix): min(Ts_Rank(decay_linear(((high+low)/2 + close < low+open), 15), 19), Ts_Rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 92.
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

ALPHA_ID = "alpha101_092"

__alpha_meta__ = {
    'id': 'alpha101_092',
    'nickname': 'Kakushadze Alpha #92',
    'theme': ['volume'],
    'formula_latex': 'min(Ts_Rank(decay_linear(((high+low)/2 + close < low+open), 15), 19), Ts_Rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 49,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    adv30 = ts_mean(volume, 30)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    cond = (((high + low) / 2.0 + close) < (low + open_)).astype(float)
    a = ts_rank(decay_linear(cond, 15), 19)
    b = ts_rank(decay_linear(ts_corr(rank(low), rank(adv30), 8), 7), 7)
    arr_a = a.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = b.to_numpy(dtype=np.float64, na_value=np.nan)
    out = pd.DataFrame(np.fmin(arr_a, arr_b), index=close.index, columns=close.columns)
    return out
