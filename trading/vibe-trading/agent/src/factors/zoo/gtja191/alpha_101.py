
# ============================================================
# 中文名称: GTJA Alpha #101
# 简要说明: 国泰君安191短周期交易型alpha因子第101号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 101 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK(CORR(close, SUM(MEAN(volume,30),37), 15)) < RANK(CORR(RANK(high), RANK(MEAN(volume,10)),11))) * -1)

Notes: Inequality cast to float via .astype('float64').
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

ALPHA_ID = "gtja191_101"

__alpha_meta__ = {
    'id': 'gtja191_101',
    'theme': ['volume', 'momentum'],
    'formula_latex': '((rank(ts\\_corr(close, sum(ts\\_mean(volume,30),37), 15)) < rank(ts\\_corr(rank(high), rank(ts\\_mean(volume,10)), 11))) * -1)',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 15,
    'min_warmup_bars': 80,
    'notes': "Inequality cast to float via .astype('float64').",
}


def compute(panel):
    """Compute gtja191_101.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    v = panel["volume"]
    left = rank(ts_corr(c, ts_mean(v, 30).rolling(37).sum(), 15))
    right = rank(ts_corr(rank(h), rank(ts_mean(v, 10)), 11))
    out = (left < right).astype("float64") * -1.0
    return out
