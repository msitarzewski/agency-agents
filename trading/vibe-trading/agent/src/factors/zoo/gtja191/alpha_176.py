
# ============================================================
# 中文名称: GTJA Alpha #176
# 简要说明: 国泰君安191短周期交易型alpha因子第176号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 176 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    CORR(RANK(((CLOSE-TSMIN(LOW,12))/(TSMAX(HIGH,12)-TSMIN(LOW,12)))),RANK(VOLUME),6)

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

ALPHA_ID = "gtja191_176"

__alpha_meta__ = {
    'id': 'gtja191_176',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 12,
    'min_warmup_bars': 18,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_176.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    ll = ts_min(l, 12)
    hh = ts_max(h, 12)
    pos = safe_div(c - ll, hh - ll)
    out = ts_corr(rank(pos), rank(v), 6)
    return out
