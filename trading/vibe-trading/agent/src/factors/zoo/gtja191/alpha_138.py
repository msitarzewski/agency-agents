
# ============================================================
# 中文名称: GTJA Alpha #138
# 简要说明: 国泰君安191短周期交易型alpha因子第138号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 138 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK(DECAYLINEAR(DELTA((((LOW*0.7)+(VWAP*0.3))),3),20))-TSRANK(DECAYLINEAR(TSRANK(CORR(TSRANK(LOW,8),TSRANK(MEAN(VOLUME,60),17),5),19),16),7))*-1)

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

ALPHA_ID = "gtja191_138"

__alpha_meta__ = {
    'id': 'gtja191_138',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 119,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_138.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    l = panel["low"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    left = rank(decay_linear(delta(l * 0.7 + vw * 0.3, 3), 20))
    inner = ts_corr(ts_rank(l, 8), ts_rank(ts_mean(v, 60), 17), 5)
    right = ts_rank(decay_linear(ts_rank(inner, 19), 16), 7)
    out = (left - right) * -1.0
    return out
