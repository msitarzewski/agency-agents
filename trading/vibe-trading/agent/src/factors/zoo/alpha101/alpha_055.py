
# ============================================================
# 中文名称: Kakushadze Alpha #55
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第55号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #55.

Formula (paper appendix): -1 * correlation(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))), rank(volume), 6)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 55.
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

ALPHA_ID = "alpha101_055"

__alpha_meta__ = {
    'id': 'alpha101_055',
    'nickname': 'Kakushadze Alpha #55',
    'theme': ['volume', 'reversal'],
    'formula_latex': '-1 * correlation(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))), rank(volume), 6)',
    'columns_required': ['high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 17,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    x = safe_div(close - ts_min(low, 12), ts_max(high, 12) - ts_min(low, 12))
    out = -1.0 * ts_corr(rank(x), rank(volume), 6)
    return out
