
# ============================================================
# 中文名称: Kakushadze Alpha #62
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第62号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #62.

Formula (paper appendix): (rank(correlation(vwap, sum(adv20,22), 10)) < rank(((rank(open)+rank(open)) < (rank((high+low)/2)+rank(high))))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 62.
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

ALPHA_ID = "alpha101_062"

__alpha_meta__ = {
    'id': 'alpha101_062',
    'nickname': 'Kakushadze Alpha #62',
    'theme': ['volume'],
    'formula_latex': '(rank(correlation(vwap, sum(adv20,22), 10)) < rank(((rank(open)+rank(open)) < (rank((high+low)/2)+rank(high))))) * -1',
    'columns_required': ['open', 'high', 'low', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 35,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    open_ = panel["open"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    lhs = rank(ts_corr(vwap, rolling_sum(adv20, 22), 10))
    inner = ((rank(open_) + rank(open_)) < (rank((high + low) / 2.0) + rank(high))).astype(float)
    rhs = rank(inner)
    out = (lhs < rhs).astype(float) * -1.0
    return out
