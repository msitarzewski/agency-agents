
# ============================================================
# 中文名称: GTJA Alpha #155
# 简要说明: 国泰君安191短周期交易型alpha因子第155号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 155 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SMA(VOLUME,13,2)-SMA(VOLUME,27,2)-SMA(SMA(VOLUME,13,2)-SMA(VOLUME,27,2),10,2)

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

ALPHA_ID = "gtja191_155"

__alpha_meta__ = {
    'id': 'gtja191_155',
    'theme': ['volume'],
    'formula_latex': 'sma(v,13,2)-sma(v,27,2)-sma(sma(v,13,2)-sma(v,27,2),10,2)',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 27,
    'min_warmup_bars': 40,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_155.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    v = panel["volume"]
    m = _sma(v, 13, 2) - _sma(v, 27, 2)
    out = m - _sma(m, 10, 2)
    return out
