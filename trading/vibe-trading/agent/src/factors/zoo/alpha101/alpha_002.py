
# ============================================================
# 中文名称: Alpha #2 - 量价相关偏差
# 简要说明: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))，量价变化的负相关性。
# 典型用途: 寻找量价关系背离的标的，负值越大意味着放量不涨或缩量不跌的反转信号。
# ============================================================
"""Kakushadze Alpha #2.

Formula (paper appendix): -1 * correlation(rank(delta(log(volume), 2)), rank(((close-open)/open)), 6)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 2.
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

ALPHA_ID = "alpha101_002"

__alpha_meta__ = {
    'id': 'alpha101_002',
    'nickname': 'Kakushadze Alpha #2',
    'theme': ['volume', 'reversal'],
    'formula_latex': '-1 * correlation(rank(delta(log(volume), 2)), rank(((close-open)/open)), 6)',
    'columns_required': ['open', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 10,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = -1.0 * ts_corr(rank(delta(np.log(volume), 2)), rank((close - open_) / open_), 6)
    return out
