
# ============================================================
# 中文名称: Kakushadze Alpha #83
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第83号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #83.

Formula (paper appendix): (rank(delay((high-low)/(sum(close,5)/5), 2)) * rank(rank(volume))) / (((high-low)/(sum(close,5)/5)) / (vwap-close))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 83.
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

ALPHA_ID = "alpha101_083"

__alpha_meta__ = {
    'id': 'alpha101_083',
    'nickname': 'Kakushadze Alpha #83',
    'theme': ['volume', 'volatility'],
    'formula_latex': '(rank(delay((high-low)/(sum(close,5)/5), 2)) * rank(rank(volume))) / (((high-low)/(sum(close,5)/5)) / (vwap-close))',
    'columns_required': ['high', 'low', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 7,
    'notes': '',
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def _delay(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Backward shift by n (lookahead-safe; n>=1 required)."""
    if n < 1:
        raise ValueError("delay requires n >= 1 (lookahead ban)")
    return df.shift(n)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    rng_avg = safe_div((high - low), rolling_sum(close, 5) / 5.0)
    num = rank(delay(rng_avg, 2)) * rank(rank(volume))
    denom = safe_div(rng_avg, vwap - close)
    out = safe_div(num, denom)
    return out
