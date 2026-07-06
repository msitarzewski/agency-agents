
# ============================================================
# 中文名称: Kakushadze Alpha #22
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第22号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #22.

Formula (paper appendix): -1 * (delta(correlation(high,volume,5),5) * rank(stddev(close,20)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 22.
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

ALPHA_ID = "alpha101_022"

__alpha_meta__ = {
    'id': 'alpha101_022',
    'nickname': 'Kakushadze Alpha #22',
    'theme': ['volume', 'volatility'],
    'formula_latex': '-1 * (delta(correlation(high,volume,5),5) * rank(stddev(close,20)))',
    'columns_required': ['high', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 25,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = -1.0 * (delta(ts_corr(high, volume, 5), 5) * rank(ts_std(close, 20)))
    return out
