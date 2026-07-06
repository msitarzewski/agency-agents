
# ============================================================
# 中文名称: Kakushadze Alpha #41
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第41号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #41.

Formula (paper appendix): (high*low)^0.5 - vwap
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 41.
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

ALPHA_ID = "alpha101_041"

__alpha_meta__ = {
    'id': 'alpha101_041',
    'nickname': 'Kakushadze Alpha #41',
    'theme': ['reversal'],
    'formula_latex': '(high*low)^0.5 - vwap',
    'columns_required': ['high', 'low', 'vwap', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 1,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    high = panel["high"]
    low = panel["low"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = (high * low).pow(0.5) - vwap
    return out
