
# ============================================================
# 中文名称: GTJA Alpha #142
# 简要说明: 国泰君安191短周期交易型alpha因子第142号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 142 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (((-1*RANK(TSRANK(CLOSE,10)))*RANK(DELTA(DELTA(CLOSE,1),1)))*RANK(TSRANK((VOLUME/MEAN(VOLUME,20)),5)))

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

ALPHA_ID = "gtja191_142"

__alpha_meta__ = {
    'id': 'gtja191_142',
    'theme': ['volume', 'reversal'],
    'formula_latex': 'see body',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 26,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_142.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    v = panel["volume"]
    a = -1.0 * rank(ts_rank(c, 10))
    b = rank(delta(delta(c, 1), 1))
    d = rank(ts_rank(safe_div(v, ts_mean(v, 20)), 5))
    out = a * b * d
    return out
