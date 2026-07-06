
# ============================================================
# 中文名称: Kakushadze Alpha #85
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第85号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #85.

Formula (paper appendix): rank(correlation(0.877*high+0.123*close, adv30, 10))^rank(correlation(Ts_Rank((high+low)/2,4), Ts_Rank(volume,10), 7))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 85.
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

ALPHA_ID = "alpha101_085"

__alpha_meta__ = {
    'id': 'alpha101_085',
    'nickname': 'Kakushadze Alpha #85',
    'theme': ['volume'],
    'formula_latex': 'rank(correlation(0.877*high+0.123*close, adv30, 10))^rank(correlation(Ts_Rank((high+low)/2,4), Ts_Rank(volume,10), 7))',
    'columns_required': ['high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 39,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    adv30 = ts_mean(volume, 30)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    mix = high * 0.876703 + close * (1.0 - 0.876703)
    lhs = rank(ts_corr(mix, adv30, 10))
    rhs = rank(ts_corr(ts_rank((high + low) / 2.0, 4), ts_rank(volume, 10), 7))
    out = lhs * rhs
    return out
