
# ============================================================
# 中文名称: GTJA Alpha #117
# 简要说明: 国泰君安191短周期交易型alpha因子第117号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 117 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(RET, 32)))

Notes: ret = close/delay(close,1) - 1.
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

ALPHA_ID = "gtja191_117"

__alpha_meta__ = {
    'id': 'gtja191_117',
    'theme': ['volume', 'momentum'],
    'formula_latex': 'tsrank(v,32)*(1-tsrank(c+h-l,16))*(1-tsrank(ret,32))',
    'columns_required': ['close', 'high', 'low', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 32,
    'min_warmup_bars': 33,
    'notes': 'ret = close/delay(close,1) - 1.',
}


def compute(panel):
    """Compute gtja191_117.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    ret = safe_div(c, c.shift(1)) - 1.0
    out = (ts_rank(v, 32) * (1.0 - ts_rank((c + h) - l, 16))) * (1.0 - ts_rank(ret, 32))
    return out
