
# ============================================================
# 中文名称: GTJA Alpha #114
# 简要说明: 国泰君安191短周期交易型alpha因子第114号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 114 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK(DELAY(((HIGH-LOW)/(SUM(CLOSE,5)/5)),2)) * RANK(RANK(VOLUME))) / (((HIGH-LOW)/(SUM(CLOSE,5)/5))/(VWAP-CLOSE)))

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

ALPHA_ID = "gtja191_114"

__alpha_meta__ = {
    'id': 'gtja191_114',
    'theme': ['volume', 'volatility'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 7,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_114.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    hl_ratio = safe_div(h - l, c.rolling(5).sum() / 5.0)
    num = rank(hl_ratio.shift(2)) * rank(rank(v))
    den = safe_div(hl_ratio, vw - c)
    out = safe_div(num, den)
    return out
