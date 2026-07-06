
# ============================================================
# 中文名称: Kakushadze Alpha #65
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第65号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #65.

Formula (paper appendix): (rank(correlation(0.008*open+0.992*vwap, sum(adv60,9), 6)) < rank(open-ts_min(open,14))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 65.
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

ALPHA_ID = "alpha101_065"

__alpha_meta__ = {
    'id': 'alpha101_065',
    'nickname': 'Kakushadze Alpha #65',
    'theme': ['volume'],
    'formula_latex': '(rank(correlation(0.008*open+0.992*vwap, sum(adv60,9), 6)) < rank(open-ts_min(open,14))) * -1',
    'columns_required': ['open', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 65,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    open_ = panel["open"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv60 = ts_mean(volume, 60)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    mix = open_ * 0.00817205 + vwap * (1.0 - 0.00817205)
    lhs = rank(ts_corr(mix, rolling_sum(adv60, 9), 6))
    rhs = rank(open_ - ts_min(open_, 14))
    out = (lhs < rhs).astype(float) * -1.0
    return out
