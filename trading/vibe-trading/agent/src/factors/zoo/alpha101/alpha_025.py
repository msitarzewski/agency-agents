
# ============================================================
# 中文名称: Kakushadze Alpha #25
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第25号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #25.

Formula (paper appendix): rank((((-1*returns)*adv20)*vwap)*(high-close))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 25.
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

ALPHA_ID = "alpha101_025"

__alpha_meta__ = {
    'id': 'alpha101_025',
    'nickname': 'Kakushadze Alpha #25',
    'theme': ['momentum', 'volume'],
    'formula_latex': 'rank((((-1*returns)*adv20)*vwap)*(high-close))',
    'columns_required': ['high', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv20 = ts_mean(volume, 20)
    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = rank(((-1.0 * returns) * adv20) * vwap * (high - close))
    return out
