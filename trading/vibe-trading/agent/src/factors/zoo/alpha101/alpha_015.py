
# ============================================================
# 中文名称: Kakushadze Alpha #15
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第15号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #15.

Formula (paper appendix): -1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 15.
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

ALPHA_ID = "alpha101_015"

__alpha_meta__ = {
    'id': 'alpha101_015',
    'nickname': 'Kakushadze Alpha #15',
    'theme': ['volume'],
    'formula_latex': '-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)',
    'columns_required': ['high', 'volume', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 6,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    high = panel["high"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    out = -1.0 * rolling_sum(rank(ts_corr(rank(high), rank(volume), 3)), 3)
    return out
