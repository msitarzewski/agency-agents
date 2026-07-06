
# ============================================================
# 中文名称: Kakushadze Alpha #39
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第39号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #39.

Formula (paper appendix): (-1*rank(delta(close,7)*(1-rank(decay_linear(volume/adv20,9))))) * (1+rank(sum(returns,250)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 39.
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

ALPHA_ID = "alpha101_039"

__alpha_meta__ = {
    'id': 'alpha101_039',
    'nickname': 'Kakushadze Alpha #39',
    'theme': ['momentum', 'volume'],
    'formula_latex': '(-1*rank(delta(close,7)*(1-rank(decay_linear(volume/adv20,9))))) * (1+rank(sum(returns,250)))',
    'columns_required': ['close', 'volume'],
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


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)
    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    out = (-1.0 * rank(delta(close, 7) * (1.0 - rank(decay_linear(safe_div(volume, adv20), 9))))) * (1.0 + rank(rolling_sum(returns, 250)))
    return out
