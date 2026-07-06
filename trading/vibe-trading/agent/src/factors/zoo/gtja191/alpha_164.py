
# ============================================================
# 中文名称: GTJA Alpha #164
# 简要说明: 国泰君安191短周期交易型alpha因子第164号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 164 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SMA(((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1) - MIN(...,12))/(HIGH-LOW)*100, 13, 2)

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

ALPHA_ID = "gtja191_164"

__alpha_meta__ = {
    'id': 'gtja191_164',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 13,
    'min_warmup_bars': 20,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_164.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    dc = c - c.shift(1)
    inv = safe_div(pd.DataFrame(np.ones_like(c, dtype=np.float64), index=c.index, columns=c.columns), dc)
    val = inv.where(dc > 0, 1.0)
    x = safe_div(val - ts_min(val, 12), (h - l)) * 100.0
    out = _sma(x, 13, 2)
    return out
