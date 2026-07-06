
# ============================================================
# 中文名称: Kakushadze Alpha #101
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第101号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #101.

Formula (paper appendix): (close - open) / ((high - low) + 0.001)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 101.
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

ALPHA_ID = "alpha101_101"

__alpha_meta__ = {
    'id': 'alpha101_101',
    'nickname': 'Kakushadze Alpha #101',
    'theme': ['reversal'],
    'formula_latex': '(close - open) / ((high - low) + 0.001)',
    'columns_required': ['open', 'high', 'low', 'close'],
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
    close = panel["close"]
    open_ = panel["open"]
    high = panel["high"]
    low = panel["low"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = safe_div((close - open_), (high - low + 0.001))
    return out
