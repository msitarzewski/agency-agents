
# ============================================================
# 中文名称: Kakushadze Alpha #74
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第74号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #74.

Formula (paper appendix): (rank(correlation(close, sum(adv30,37), 15)) < rank(correlation(rank(0.026*high+0.974*vwap), rank(volume), 11))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 74.
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

ALPHA_ID = "alpha101_074"

__alpha_meta__ = {
    'id': 'alpha101_074',
    'nickname': 'Kakushadze Alpha #74',
    'theme': ['volume'],
    'formula_latex': '(rank(correlation(close, sum(adv30,37), 15)) < rank(correlation(rank(0.026*high+0.974*vwap), rank(volume), 11))) * -1',
    'columns_required': ['high', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 60,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv30 = ts_mean(volume, 30)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    lhs = rank(ts_corr(close, rolling_sum(adv30, 37), 15))
    mix = high * 0.0261661 + vwap * (1.0 - 0.0261661)
    rhs = rank(ts_corr(rank(mix), rank(volume), 11))
    out = (lhs < rhs).astype(float) * -1.0
    return out
