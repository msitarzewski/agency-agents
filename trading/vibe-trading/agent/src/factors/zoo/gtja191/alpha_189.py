
# ============================================================
# 中文名称: GTJA Alpha #189
# 简要说明: 国泰君安191短周期交易型alpha因子第189号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 189 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)

Notes: 
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

ALPHA_ID = "gtja191_189"

__alpha_meta__ = {
    'id': 'gtja191_189',
    'theme': ['volatility'],
    'formula_latex': 'mean(abs(c-mean(c,6)),6)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 6,
    'min_warmup_bars': 12,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_189.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    out = ts_mean((c - ts_mean(c, 6)).abs(), 6)
    return out
