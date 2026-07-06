
# ============================================================
# 中文名称: Kakushadze Alpha #86
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第86号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #86.

Formula (paper appendix): (Ts_Rank(correlation(close, sum(adv20,15), 6), 20) < rank((open+close) - (vwap+open))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 86.
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

ALPHA_ID = "alpha101_086"

__alpha_meta__ = {
    'id': 'alpha101_086',
    'nickname': 'Kakushadze Alpha #86',
    'theme': ['volume'],
    'formula_latex': '(Ts_Rank(correlation(close, sum(adv20,15), 6), 20) < rank((open+close) - (vwap+open))) * -1',
    'columns_required': ['open', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 44,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    lhs = ts_rank(ts_corr(close, rolling_sum(adv20, 15), 6), 20)
    rhs = rank((open_ + close) - (vwap + open_))
    out = (lhs < rhs).astype(float) * -1.0
    return out
