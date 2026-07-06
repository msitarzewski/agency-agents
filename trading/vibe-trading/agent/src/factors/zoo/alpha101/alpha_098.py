
# ============================================================
# 中文名称: Kakushadze Alpha #98
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第98号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #98.

Formula (paper appendix): rank(decay_linear(correlation(vwap, sum(adv5,26), 5), 7)) - rank(decay_linear(Ts_Rank(Ts_ArgMin(correlation(rank(open), rank(adv15), 21), 9), 7), 8))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 98.
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

ALPHA_ID = "alpha101_098"

__alpha_meta__ = {
    'id': 'alpha101_098',
    'nickname': 'Kakushadze Alpha #98',
    'theme': ['volume'],
    'formula_latex': 'rank(decay_linear(correlation(vwap, sum(adv5,26), 5), 7)) - rank(decay_linear(Ts_Rank(Ts_ArgMin(correlation(rank(open), rank(adv15), 21), 9), 7), 8))',
    'columns_required': ['open', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 56,
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
    adv5 = ts_mean(volume, 5)
    adv15 = ts_mean(volume, 15)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    a = rank(decay_linear(ts_corr(vwap, rolling_sum(adv5, 26), 5), 7))
    b = rank(decay_linear(ts_rank(ts_argmin(ts_corr(rank(open_), rank(adv15), 21), 9), 7), 8))
    out = a - b
    return out
