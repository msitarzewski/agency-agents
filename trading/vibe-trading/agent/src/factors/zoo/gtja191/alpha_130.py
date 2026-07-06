
# ============================================================
# 中文名称: GTJA Alpha #130
# 简要说明: 国泰君安191短周期交易型alpha因子第130号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 130 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (RANK(DECAYLINEAR(CORR((H+L)/2,MEAN(V,40),9),10))/RANK(DECAYLINEAR(CORR(RANK(VWAP),RANK(V),7),3)))

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

ALPHA_ID = "gtja191_130"

__alpha_meta__ = {
    'id': 'gtja191_130',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 40,
    'min_warmup_bars': 60,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_130.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    num = rank(decay_linear(ts_corr((h + l) / 2.0, ts_mean(v, 40), 9), 10))
    den = rank(decay_linear(ts_corr(rank(vw), rank(v), 7), 3))
    out = safe_div(num, den)
    return out
