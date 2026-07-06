
# ============================================================
# 中文名称: Kakushadze Alpha #35
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第35号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #35.

Formula (paper appendix): ts_rank(volume,32) * (1 - ts_rank((close+high-low),16)) * (1 - ts_rank(returns,32))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 35.
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

ALPHA_ID = "alpha101_035"

__alpha_meta__ = {
    'id': 'alpha101_035',
    'nickname': 'Kakushadze Alpha #35',
    'theme': ['volume', 'momentum'],
    'formula_latex': 'ts_rank(volume,32) * (1 - ts_rank((close+high-low),16)) * (1 - ts_rank(returns,32))',
    'columns_required': ['high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 33,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]

    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = ts_rank(volume, 32) * (1.0 - ts_rank((close + high - low), 16)) * (1.0 - ts_rank(returns, 32))
    return out
