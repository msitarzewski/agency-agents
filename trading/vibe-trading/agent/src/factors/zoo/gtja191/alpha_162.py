
# ============================================================
# 中文名称: GTJA Alpha #162
# 简要说明: 国泰君安191短周期交易型alpha因子第162号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 162 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100 - MIN(...,12)) / (MAX(...,12) - MIN(...,12))

Notes: RSI-style normalised.
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

ALPHA_ID = "gtja191_162"

__alpha_meta__ = {
    'id': 'gtja191_162',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 12,
    'min_warmup_bars': 24,
    'notes': 'RSI-style normalised.',
}


def compute(panel):
    """Compute gtja191_162.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    c = panel["close"]
    dc = c - c.shift(1)
    rsi = safe_div(_sma(dc.clip(lower=0.0), 12, 1), _sma(dc.abs(), 12, 1)) * 100.0
    out = safe_div(rsi - ts_min(rsi, 12), ts_max(rsi, 12) - ts_min(rsi, 12))
    return out
