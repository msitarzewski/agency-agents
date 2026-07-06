
# ============================================================
# 中文名称: Kakushadze Alpha #95
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第95号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #95.

Formula (paper appendix): rank(open-ts_min(open,13)) < Ts_Rank((rank(correlation(sum((high+low)/2,19), sum(adv40,19),13))^5), 12)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 95.
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

ALPHA_ID = "alpha101_095"

__alpha_meta__ = {
    'id': 'alpha101_095',
    'nickname': 'Kakushadze Alpha #95',
    'theme': ['volume'],
    'formula_latex': 'rank(open-ts_min(open,13)) < Ts_Rank((rank(correlation(sum((high+low)/2,19), sum(adv40,19),13))^5), 12)',
    'columns_required': ['open', 'high', 'low', 'volume', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 63,
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
    adv40 = ts_mean(volume, 40)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    lhs = rank(open_ - ts_min(open_, 13))
    inner = rank(ts_corr(rolling_sum((high + low) / 2.0, 19), rolling_sum(adv40, 19), 13))
    inner = signed_power(inner, 5.0)
    rhs = ts_rank(inner, 12)
    out = (lhs < rhs).astype(float)
    return out
