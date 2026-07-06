
# ============================================================
# 中文名称: Alpha #6 - 开盘收益率相关
# 简要说明: (-1 * correlation(open, volume, 10))，开盘价与成交量的负相关。
# 典型用途: 开盘量价背离信号，常用于开盘反转策略。
# ============================================================
"""Kakushadze Alpha #6.

Formula (paper appendix): -1 * correlation(open, volume, 10)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 6.
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

ALPHA_ID = "alpha101_006"

__alpha_meta__ = {
    'id': 'alpha101_006',
    'nickname': 'Kakushadze Alpha #6',
    'theme': ['volume', 'reversal'],
    'formula_latex': '-1 * correlation(open, volume, 10)',
    'columns_required': ['open', 'volume', 'close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 10,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    open_ = panel["open"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = -1.0 * ts_corr(open_, volume, 10)
    return out
