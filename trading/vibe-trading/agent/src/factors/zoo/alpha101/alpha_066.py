
# ============================================================
# 中文名称: Kakushadze Alpha #66
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第66号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #66.

Formula (paper appendix): (rank(decay_linear(delta(vwap,4), 7)) + Ts_Rank(decay_linear(((0.966*low+0.034*low - vwap)/(open-(high+low)/2)), 11), 7)) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 66.
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

ALPHA_ID = "alpha101_066"

__alpha_meta__ = {
    'id': 'alpha101_066',
    'nickname': 'Kakushadze Alpha #66',
    'theme': ['momentum'],
    'formula_latex': '(rank(decay_linear(delta(vwap,4), 7)) + Ts_Rank(decay_linear(((0.966*low+0.034*low - vwap)/(open-(high+low)/2)), 11), 7)) * -1',
    'columns_required': ['open', 'high', 'low', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 18,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    open_ = panel["open"]
    high = panel["high"]
    low = panel["low"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    t1 = rank(decay_linear(delta(vwap, 4), 7))
    num = (low * 0.96633 + low * (1.0 - 0.96633)) - vwap
    denom = open_ - (high + low) / 2.0
    t2 = ts_rank(decay_linear(safe_div(num, denom), 11), 7)
    out = (t1 + t2) * -1.0
    return out
