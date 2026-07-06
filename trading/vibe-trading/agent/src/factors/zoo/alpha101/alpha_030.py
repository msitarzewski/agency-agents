
# ============================================================
# 中文名称: Kakushadze Alpha #30
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第30号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #30.

Formula (paper appendix): ((1-rank(sign(d1)+sign(d2)+sign(d3))) * sum(volume,5)) / sum(volume,20)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 30.
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

ALPHA_ID = "alpha101_030"

__alpha_meta__ = {
    'id': 'alpha101_030',
    'nickname': 'Kakushadze Alpha #30',
    'theme': ['momentum', 'volume'],
    'formula_latex': '((1-rank(sign(d1)+sign(d2)+sign(d3))) * sum(volume,5)) / sum(volume,20)',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 20,
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
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    s = np.sign(close - delay(close, 1)) + np.sign(delay(close, 1) - delay(close, 2)) + np.sign(delay(close, 2) - delay(close, 3))
    out = safe_div((1.0 - rank(s)) * rolling_sum(volume, 5), rolling_sum(volume, 20))
    return out
