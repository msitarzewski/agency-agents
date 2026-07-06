
# ============================================================
# 中文名称: Kakushadze Alpha #81
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第81号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #81.

Formula (paper appendix): (rank(Log(product(rank((rank(correlation(vwap, sum(adv10,50), 8))^4)), 15))) < rank(correlation(rank(vwap), rank(volume), 5))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 81.
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

ALPHA_ID = "alpha101_081"

__alpha_meta__ = {
    'id': 'alpha101_081',
    'nickname': 'Kakushadze Alpha #81',
    'theme': ['volume'],
    'formula_latex': '(rank(Log(product(rank((rank(correlation(vwap, sum(adv10,50), 8))^4)), 15))) < rank(correlation(rank(vwap), rank(volume), 5))) * -1',
    'columns_required': ['volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 70,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def _rolling_prod(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window product; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).apply(np.prod, raw=True)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv10 = ts_mean(volume, 10)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    rolling_prod = _rolling_prod
    inner = rank(ts_corr(vwap, rolling_sum(adv10, 50), 8))
    inner = signed_power(inner, 4.0)
    inner = rank(inner)
    prod = rolling_prod(inner, 15)
    lhs = rank(np.log(prod.where(prod > 0)))
    rhs = rank(ts_corr(rank(vwap), rank(volume), 5))
    out = (lhs < rhs).astype(float) * -1.0
    return out
