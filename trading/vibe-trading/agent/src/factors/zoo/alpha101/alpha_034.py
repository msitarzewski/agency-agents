
# ============================================================
# 中文名称: Kakushadze Alpha #34
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第34号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #34.

Formula (paper appendix): rank((1-rank(stddev(returns,2)/stddev(returns,5))) + (1-rank(delta(close,1))))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 34.
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

ALPHA_ID = "alpha101_034"

__alpha_meta__ = {
    'id': 'alpha101_034',
    'nickname': 'Kakushadze Alpha #34',
    'theme': ['volatility'],
    'formula_latex': 'rank((1-rank(stddev(returns,2)/stddev(returns,5))) + (1-rank(delta(close,1))))',
    'columns_required': ['close'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 6,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]


    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = rank((1.0 - rank(safe_div(ts_std(returns, 2), ts_std(returns, 5)))) + (1.0 - rank(delta(close, 1))))
    return out
