
# ============================================================
# 中文名称: Kakushadze Alpha #28
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第28号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #28.

Formula (paper appendix): scale((correlation(adv20,low,5) + (high+low)/2) - close)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 28.
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

ALPHA_ID = "alpha101_028"

__alpha_meta__ = {
    'id': 'alpha101_028',
    'nickname': 'Kakushadze Alpha #28',
    'theme': ['volume'],
    'formula_latex': 'scale((correlation(adv20,low,5) + (high+low)/2) - close)',
    'columns_required': ['high', 'low', 'close', 'volume'],
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
    low = panel["low"]
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = scale(ts_corr(adv20, low, 5) + (high + low) / 2.0 - close)
    return out
