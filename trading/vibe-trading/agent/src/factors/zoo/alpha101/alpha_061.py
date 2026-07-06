
# ============================================================
# 中文名称: Kakushadze Alpha #61
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第61号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #61.

Formula (paper appendix): rank(vwap - ts_min(vwap,16)) < rank(correlation(vwap, adv180, 18))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 61.
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

ALPHA_ID = "alpha101_061"

__alpha_meta__ = {
    'id': 'alpha101_061',
    'nickname': 'Kakushadze Alpha #61',
    'theme': ['volume'],
    'formula_latex': 'rank(vwap - ts_min(vwap,16)) < rank(correlation(vwap, adv180, 18))',
    'columns_required': ['volume', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 197,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv180 = ts_mean(volume, 180)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    lhs = rank(vwap - ts_min(vwap, 16))
    rhs = rank(ts_corr(vwap, adv180, 18))
    out = (lhs < rhs).astype(float)
    return out
