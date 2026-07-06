
# ============================================================
# 中文名称: Kakushadze Alpha #68
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第68号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #68.

Formula (paper appendix): (Ts_Rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta(0.518*close+0.482*low, 1))) * -1
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 68.
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

ALPHA_ID = "alpha101_068"

__alpha_meta__ = {
    'id': 'alpha101_068',
    'nickname': 'Kakushadze Alpha #68',
    'theme': ['volume'],
    'formula_latex': '(Ts_Rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta(0.518*close+0.482*low, 1))) * -1',
    'columns_required': ['high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 36,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    adv15 = ts_mean(volume, 15)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    lhs = ts_rank(ts_corr(rank(high), rank(adv15), 9), 14)
    mix = close * 0.518371 + low * (1.0 - 0.518371)
    rhs = rank(delta(mix, 1))
    out = (lhs < rhs).astype(float) * -1.0
    return out
