
# ============================================================
# 中文名称: GTJA Alpha #179
# 简要说明: 国泰君安191短周期交易型alpha因子第179号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 179 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    RANK(CORR(VWAP,VOLUME,4))*RANK(CORR(RANK(LOW),RANK(MEAN(VOLUME,50)),12))

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

ALPHA_ID = "gtja191_179"

__alpha_meta__ = {
    'id': 'gtja191_179',
    'theme': ['volume'],
    'formula_latex': 'rank(corr(vwap,v,4))*rank(corr(rank(low),rank(mean(v,50)),12))',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 50,
    'min_warmup_bars': 62,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_179.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    l = panel["low"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    out = rank(ts_corr(vw, v, 4)) * rank(ts_corr(rank(l), rank(ts_mean(v, 50)), 12))
    return out
