
# ============================================================
# 中文名称: GTJA Alpha #124
# 简要说明: 国泰君安191短周期交易型alpha因子第124号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 124 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (CLOSE-VWAP)/DECAYLINEAR(RANK(TSMAX(CLOSE,30)),2)

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

ALPHA_ID = "gtja191_124"

__alpha_meta__ = {
    'id': 'gtja191_124',
    'theme': ['reversal'],
    'formula_latex': '(close-vwap)/decay_linear(rank(tsmax(close,30)),2)',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 32,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_124.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    vw = vwap(panel, "equity_cn")

    out = safe_div(c - vw, decay_linear(rank(ts_max(c, 30)), 2))
    return out
