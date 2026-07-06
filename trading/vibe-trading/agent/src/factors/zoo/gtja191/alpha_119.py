
# ============================================================
# 中文名称: GTJA Alpha #119
# 简要说明: 国泰君安191短周期交易型alpha因子第119号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 119 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    RANK(DECAYLINEAR(CORR(VWAP,SUM(MEAN(VOLUME,5),26),5),7)) - RANK(DECAYLINEAR(TSRANK(MIN(CORR(RANK(OPEN),RANK(MEAN(VOLUME,15)),21),9),7),8))

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
    vwap,
)

ALPHA_ID = "gtja191_119"

__alpha_meta__ = {
    'id': 'gtja191_119',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 26,
    'min_warmup_bars': 60,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_119.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    left = rank(decay_linear(ts_corr(vw, ts_mean(v, 5).rolling(26).sum(), 5), 7))
    inner = ts_min(ts_corr(rank(o), rank(ts_mean(v, 15)), 21), 9)
    right = rank(decay_linear(ts_rank(inner, 7), 8))
    out = left - right
    return out
