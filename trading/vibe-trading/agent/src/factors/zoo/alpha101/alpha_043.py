
# ============================================================
# 中文名称: Kakushadze Alpha #43
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第43号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #43.

Formula (paper appendix): ts_rank(volume/adv20,20) * ts_rank(-1*delta(close,7),8)
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 43.
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

ALPHA_ID = "alpha101_043"

__alpha_meta__ = {
    'id': 'alpha101_043',
    'nickname': 'Kakushadze Alpha #43',
    'theme': ['volume', 'momentum'],
    'formula_latex': 'ts_rank(volume/adv20,20) * ts_rank(-1*delta(close,7),8)',
    'columns_required': ['close', 'volume'],
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
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    out = ts_rank(safe_div(volume, adv20), 20) * ts_rank(-1.0 * delta(close, 7), 8)
    return out
