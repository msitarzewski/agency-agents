
# ============================================================
# 中文名称: Alpha #4 - 条件收益指示
# 简要说明: (-1 * Ts_Rank(rank(low), 9))，对最低价的9日时间序列排名取负。
# 典型用途: 当价格持续创新低时该值较低，用于超跌反弹策略。
# ============================================================
"""Kakushadze Alpha #4.

Formula (paper appendix): -1 * Ts_Rank(rank(low), 9)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 4.
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

ALPHA_ID = "alpha101_004"

__alpha_meta__ = {
    'id': 'alpha101_004',
    'nickname': 'Kakushadze Alpha #4',
    'theme': ['reversal'],
    'formula_latex': '-1 * Ts_Rank(rank(low), 9)',
    'columns_required': ['low', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 9,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    low = panel["low"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = -1.0 * ts_rank(rank(low), 9)
    return out
