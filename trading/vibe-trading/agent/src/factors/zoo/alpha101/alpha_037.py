
# ============================================================
# 中文名称: Kakushadze Alpha #37
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第37号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #37.

Formula (paper appendix): rank(correlation(delay(open-close,1),close,200)) + rank(open-close)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 37.
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

ALPHA_ID = "alpha101_037"

__alpha_meta__ = {
    'id': 'alpha101_037',
    'nickname': 'Kakushadze Alpha #37',
    'theme': ['momentum'],
    'formula_latex': 'rank(correlation(delay(open-close,1),close,200)) + rank(open-close)',
    'columns_required': ['open', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 201,
    'notes': 'Very long lookback (>= ~100 bars); produces NaN warmup on short panels which may trigger the >95% NaN registry guard.',
}


def _delay(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Backward shift by n (lookahead-safe; n>=1 required)."""
    if n < 1:
        raise ValueError("delay requires n >= 1 (lookahead ban)")
    return df.shift(n)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    delay = _delay
    out = rank(ts_corr(delay(open_ - close, 1), close, 200)) + rank(open_ - close)
    return out
