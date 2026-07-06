
# ============================================================
# 中文名称: Kakushadze Alpha #12
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第12号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #12.

Formula (paper appendix): sign(delta(volume,1)) * (-1 * delta(close,1))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 12.
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

ALPHA_ID = "alpha101_012"

__alpha_meta__ = {
    'id': 'alpha101_012',
    'nickname': 'Kakushadze Alpha #12',
    'theme': ['volume', 'reversal'],
    'formula_latex': 'sign(delta(volume,1)) * (-1 * delta(close,1))',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 2,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    volume = panel["volume"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = np.sign(delta(volume, 1)) * (-1.0 * delta(close, 1))
    return out
