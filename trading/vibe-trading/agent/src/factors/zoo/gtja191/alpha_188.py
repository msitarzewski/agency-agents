
# ============================================================
# 中文名称: GTJA Alpha #188
# 简要说明: 国泰君安191短周期交易型alpha因子第188号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 188 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2)*100

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

ALPHA_ID = "gtja191_188"

__alpha_meta__ = {
    'id': 'gtja191_188',
    'theme': ['volatility'],
    'formula_latex': '(h-l-sma(h-l,11,2))/sma(h-l,11,2)*100',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 11,
    'min_warmup_bars': 13,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_188.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    h = panel["high"]
    l = panel["low"]
    hl = h - l
    s = _sma(hl, 11, 2)
    out = safe_div(hl - s, s) * 100.0
    return out
