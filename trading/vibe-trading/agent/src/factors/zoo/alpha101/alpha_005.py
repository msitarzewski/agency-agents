
# ============================================================
# 中文名称: Alpha #5 - 高低价差动量
# 简要说明: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap))))) ，开盘价与VWAP均值的偏离乘以收盘价偏离的绝对值取负。
# 典型用途: 综合衡量开盘和收盘相对于VWAP的偏离方向，用于趋势延续性判断。
# ============================================================
"""Kakushadze Alpha #5.

Formula (paper appendix): rank((open - sum(vwap,10)/10)) * (-1 * abs(rank((close - vwap))))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 5.
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

ALPHA_ID = "alpha101_005"

__alpha_meta__ = {
    'id': 'alpha101_005',
    'nickname': 'Kakushadze Alpha #5',
    'theme': ['reversal'],
    'formula_latex': 'rank((open - sum(vwap,10)/10)) * (-1 * abs(rank((close - vwap))))',
    'columns_required': ['open', 'close', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 10,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    out = rank(open_ - rolling_sum(vwap, 10) / 10.0) * (-1.0 * rank(close - vwap).abs())
    return out
