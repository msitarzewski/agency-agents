
# ============================================================
# 中文名称: Kakushadze Alpha #73
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第73号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #73.

Formula (paper appendix): max(rank(decay_linear(delta(vwap,5), 3)), Ts_Rank(decay_linear(-1*(delta(0.147*open+0.853*low,2)/(0.147*open+0.853*low)), 3), 17)) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 73.
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

ALPHA_ID = "alpha101_073"

__alpha_meta__ = {
    'id': 'alpha101_073',
    'nickname': 'Kakushadze Alpha #73',
    'theme': ['volume'],
    'formula_latex': 'max(rank(decay_linear(delta(vwap,5), 3)), Ts_Rank(decay_linear(-1*(delta(0.147*open+0.853*low,2)/(0.147*open+0.853*low)), 3), 17)) * -1',
    'columns_required': ['open', 'low', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    low = panel["low"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    a = rank(decay_linear(delta(vwap, 5), 3))
    mix = open_ * 0.147155 + low * (1.0 - 0.147155)
    b_inner = safe_div(delta(mix, 2), mix) * -1.0
    b = ts_rank(decay_linear(b_inner, 3), 17)
    arr_a = a.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = b.to_numpy(dtype=np.float64, na_value=np.nan)
    out = pd.DataFrame(np.fmax(arr_a, arr_b), index=close.index, columns=close.columns) * -1.0
    return out
