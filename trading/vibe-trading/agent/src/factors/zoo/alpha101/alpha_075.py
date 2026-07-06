
# ============================================================
# 中文名称: Kakushadze Alpha #75
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第75号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #75.

Formula (paper appendix): rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 75.
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

ALPHA_ID = "alpha101_075"

__alpha_meta__ = {
    'id': 'alpha101_075',
    'nickname': 'Kakushadze Alpha #75',
    'theme': ['volume'],
    'formula_latex': 'rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12))',
    'columns_required': ['low', 'volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 61,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv5 = ts_mean(volume, 5)
    adv50 = ts_mean(volume, 50)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    lhs = rank(ts_corr(vwap, volume, 4))
    rhs = rank(ts_corr(rank(low), rank(adv50), 12))
    out = (lhs < rhs).astype(float)
    return out
