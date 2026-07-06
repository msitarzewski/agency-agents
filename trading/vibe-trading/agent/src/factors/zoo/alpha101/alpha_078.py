
# ============================================================
# 中文名称: Kakushadze Alpha #78
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第78号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #78.

Formula (paper appendix): rank(correlation(sum(0.352*low+0.648*vwap, 20), sum(adv40,20), 7))^rank(correlation(rank(vwap), rank(volume), 6))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 78.
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

ALPHA_ID = "alpha101_078"

__alpha_meta__ = {
    'id': 'alpha101_078',
    'nickname': 'Kakushadze Alpha #78',
    'theme': ['volume'],
    'formula_latex': 'rank(correlation(sum(0.352*low+0.648*vwap, 20), sum(adv40,20), 7))^rank(correlation(rank(vwap), rank(volume), 6))',
    'columns_required': ['low', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 46,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv40 = ts_mean(volume, 40)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    mix = low * 0.352233 + vwap * (1.0 - 0.352233)
    lhs = rank(ts_corr(rolling_sum(mix, 20), rolling_sum(adv40, 20), 7))
    rhs = rank(ts_corr(rank(vwap), rank(volume), 6))
    out = lhs * rhs
    return out
