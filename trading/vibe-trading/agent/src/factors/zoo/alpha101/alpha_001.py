
# ============================================================
# 中文名称: Alpha #1 - 收益条件动量
# 简要说明: rank(ts_argmax(SignedPower((returns<0)?stddev(returns,20):close, 2.), 5)) - 0.5，基于收益与波动的时间序列动量。
# 典型用途: 识别收益加速或波动条件改善的股票，做多排名靠前、做空排名靠后的标的。
# ============================================================
"""Kakushadze Alpha #1.

Formula (paper appendix): rank(ts_argmax(SignedPower((returns<0)?stddev(returns,20):close, 2.), 5)) - 0.5
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 1.
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

ALPHA_ID = "alpha101_001"

__alpha_meta__ = {
    'id': 'alpha101_001',
    'nickname': 'Kakushadze Alpha #1',
    'theme': ['reversal', 'volatility'],
    'formula_latex': 'rank(ts_argmax(SignedPower((returns<0)?stddev(returns,20):close, 2.), 5)) - 0.5',
    'columns_required': ['close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 25,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]


    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    cond = (returns < 0).astype(float)
    x = ts_std(returns, 20) * cond + close * (1.0 - cond)
    out = rank(ts_argmax(signed_power(x, 2.0), 5)) - 0.5
    return out
