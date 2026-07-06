
# ============================================================
# 中文名称: Kakushadze Alpha #20
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第20号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #20.

Formula (paper appendix): (((-1*rank(open-delay(high,1)))*rank(open-delay(close,1)))*rank(open-delay(low,1)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 20.
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

ALPHA_ID = "alpha101_020"

__alpha_meta__ = {
    'id': 'alpha101_020',
    'nickname': 'Kakushadze Alpha #20',
    'theme': ['reversal'],
    'formula_latex': '(((-1*rank(open-delay(high,1)))*rank(open-delay(close,1)))*rank(open-delay(low,1)))',
    'columns_required': ['open', 'high', 'low', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 2,
    'notes': '',
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
    high = panel["high"]
    low = panel["low"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    delay = _delay
    out = ((-1.0 * rank(open_ - delay(high, 1))) * rank(open_ - delay(close, 1))) * rank(open_ - delay(low, 1))
    return out
