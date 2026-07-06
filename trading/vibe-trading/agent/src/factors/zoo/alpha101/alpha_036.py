
# ============================================================
# 中文名称: Kakushadze Alpha #36
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第36号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #36.

Formula (paper appendix): weighted sum; see paper
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 36.
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

ALPHA_ID = "alpha101_036"

__alpha_meta__ = {
    'id': 'alpha101_036',
    'nickname': 'Kakushadze Alpha #36',
    'theme': ['momentum', 'volume'],
    'formula_latex': 'weighted sum; see paper',
    'columns_required': ['open', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 200,
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
    open_ = panel["open"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv20 = ts_mean(volume, 20)
    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    delay = _delay
    t1 = 2.21 * rank(ts_corr((close - open_), delay(volume, 1), 15))
    t2 = 0.7 * rank(open_ - close)
    t3 = 0.73 * rank(ts_rank(delay(-1.0 * returns, 6), 5))
    t4 = rank(ts_corr(vwap, adv20, 6).abs())
    t5 = 0.6 * rank((rolling_sum(close, 200) / 200.0 - open_) * (close - open_))
    out = t1 + t2 + t3 + t4 + t5
    return out
