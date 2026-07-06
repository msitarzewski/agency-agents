
# ============================================================
# 中文名称: Kakushadze Alpha #32
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第32号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #32.

Formula (paper appendix): scale(sum(close,7)/7 - close) + 20*scale(correlation(vwap, delay(close,5), 230))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 32.
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

ALPHA_ID = "alpha101_032"

__alpha_meta__ = {
    'id': 'alpha101_032',
    'nickname': 'Kakushadze Alpha #32',
    'theme': ['momentum'],
    'formula_latex': 'scale(sum(close,7)/7 - close) + 20*scale(correlation(vwap, delay(close,5), 230))',
    'columns_required': ['close', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 235,
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
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    out = scale(rolling_sum(close, 7) / 7.0 - close) + 20.0 * scale(ts_corr(vwap, delay(close, 5), 230))
    return out
