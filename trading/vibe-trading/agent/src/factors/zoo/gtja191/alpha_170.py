
# ============================================================
# 中文名称: GTJA Alpha #170
# 简要说明: 国泰君安191短周期交易型alpha因子第170号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 170 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((((RANK((1/CLOSE))*VOLUME)/MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH-CLOSE))) / (SUM(HIGH,5)/5))) - RANK((VWAP - DELAY(VWAP,5))))

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

ALPHA_ID = "gtja191_170"

__alpha_meta__ = {
    'id': 'gtja191_170',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_170.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    a = safe_div(rank(safe_div(pd.DataFrame(1.0, index=c.index, columns=c.columns), c)) * v, ts_mean(v, 20))
    b = safe_div(h * rank(h - c), c.rolling(5).sum() / 5.0)
    d = rank(vw - vw.shift(5))
    out = a * b - d
    return out
