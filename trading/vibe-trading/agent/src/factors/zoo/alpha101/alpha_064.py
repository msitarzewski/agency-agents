
# ============================================================
# 中文名称: Kakushadze Alpha #64
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第64号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #64.

Formula (paper appendix): (rank(correlation(sum(0.178*open+0.822*low,13), sum(adv120,13), 17)) < rank(delta(0.178*((high+low)/2)+0.822*vwap, 4))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 64.
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

ALPHA_ID = "alpha101_064"

__alpha_meta__ = {
    'id': 'alpha101_064',
    'nickname': 'Kakushadze Alpha #64',
    'theme': ['volume'],
    'formula_latex': '(rank(correlation(sum(0.178*open+0.822*low,13), sum(adv120,13), 17)) < rank(delta(0.178*((high+low)/2)+0.822*vwap, 4))) * -1',
    'columns_required': ['open', 'high', 'low', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 136,
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
    adv120 = ts_mean(volume, 120)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    a = open_ * 0.178404 + low * (1.0 - 0.178404)
    b = ((high + low) / 2.0) * 0.178404 + vwap * (1.0 - 0.178404)
    lhs = rank(ts_corr(rolling_sum(a, 13), rolling_sum(adv120, 13), 17))
    rhs = rank(delta(b, 4))
    out = (lhs < rhs).astype(float) * -1.0
    return out
