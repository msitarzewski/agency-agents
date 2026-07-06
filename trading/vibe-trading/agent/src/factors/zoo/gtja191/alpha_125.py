
# ============================================================
# 中文名称: GTJA Alpha #125
# 简要说明: 国泰君安191短周期交易型alpha因子第125号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 125 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (RANK(DECAYLINEAR(CORR(VWAP,MEAN(VOLUME,80),17),20))/RANK(DECAYLINEAR(DELTA(((CLOSE*0.5)+(VWAP*0.5)),3),16)))

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

ALPHA_ID = "gtja191_125"

__alpha_meta__ = {
    'id': 'gtja191_125',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 120,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_125.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    num = rank(decay_linear(ts_corr(vw, ts_mean(v, 80), 17), 20))
    den = rank(decay_linear(delta(c * 0.5 + vw * 0.5, 3), 16))
    out = safe_div(num, den)
    return out
