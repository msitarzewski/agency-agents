
# ============================================================
# 中文名称: Kakushadze Alpha #19
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第19号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #19.

Formula (paper appendix): (-1*sign((close-delay(close,7))+delta(close,7))) * (1+rank(1+sum(returns,250)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 19.
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

ALPHA_ID = "alpha101_019"

__alpha_meta__ = {
    'id': 'alpha101_019',
    'nickname': 'Kakushadze Alpha #19',
    'theme': ['momentum'],
    'formula_latex': '(-1*sign((close-delay(close,7))+delta(close,7))) * (1+rank(1+sum(returns,250)))',
    'columns_required': ['close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 250,
    'notes': 'Very long lookback (>= ~100 bars); produces NaN warmup on short panels which may trigger the >95% NaN registry guard.',
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


    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    out = (-1.0 * np.sign((close - delay(close, 7)) + delta(close, 7))) * (1.0 + rank(1.0 + rolling_sum(returns, 250)))
    return out
