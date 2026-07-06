
# ============================================================
# 中文名称: GTJA Alpha #174
# 简要说明: 国泰君安191短周期交易型alpha因子第174号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 174 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)

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

ALPHA_ID = "gtja191_174"

__alpha_meta__ = {
    'id': 'gtja191_174',
    'theme': ['volatility'],
    'formula_latex': 'sma((c>delay(c,1)?std(c,20):0),20,1)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 22,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_174.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    c = panel["close"]
    cond = (c > c.shift(1)).astype("float64")
    out = _sma(ts_std(c, 20) * cond, 20, 1)
    return out
