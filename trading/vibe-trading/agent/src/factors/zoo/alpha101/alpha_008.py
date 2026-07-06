
# ============================================================
# 中文名称: Alpha #8 - 收益波动对冲
# 简要说明: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))，开盘累计与收益累计的滞后差。
# 典型用途: 检测开盘价趋势与收益率趋势的变化速度差异，用于趋势反转预警。
# ============================================================
"""Kakushadze Alpha #8.

Formula (paper appendix): -1 * rank((sum(open,5)*sum(returns,5)) - delay(sum(open,5)*sum(returns,5),10))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 8.
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

ALPHA_ID = "alpha101_008"

__alpha_meta__ = {
    'id': 'alpha101_008',
    'nickname': 'Kakushadze Alpha #8',
    'theme': ['reversal'],
    'formula_latex': '-1 * rank((sum(open,5)*sum(returns,5)) - delay(sum(open,5)*sum(returns,5),10))',
    'columns_required': ['open', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 15,
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
    open_ = panel["open"]

    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    s = rolling_sum(open_, 5) * rolling_sum(returns, 5)
    out = -1.0 * rank(s - delay(s, 10))
    return out
