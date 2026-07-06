
# ============================================================
# 中文名称: GTJA Alpha #163
# 简要说明: 国泰君安191短周期交易型alpha因子第163号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 163 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))

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

ALPHA_ID = "gtja191_163"

__alpha_meta__ = {
    'id': 'gtja191_163',
    'theme': ['volume'],
    'formula_latex': 'rank(((-1*ret)*mean(v,20))*vwap*(high-close))',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_163.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    ret = safe_div(c, c.shift(1)) - 1.0
    out = rank(((-1.0 * ret) * ts_mean(v, 20)) * vw * (h - c))
    return out
