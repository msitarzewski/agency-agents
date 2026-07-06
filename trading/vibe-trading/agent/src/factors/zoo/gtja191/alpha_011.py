
# ============================================================
# 中文名称: GTJA #11 - 条件高低价差
# 简要说明: ((RANK(MAX((VWAP-CLOSE), 3)) + RANK(MIN((VWAP-CLOSE), 3))) * RANK(DELTA(VOLUME, 3)))，VWAP偏离极值与成交量变化的乘积。
# 典型用途: 量价配合的VWAP回归交易信号。
# ============================================================
"""GTJA Alpha #11.

Formula: SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME,6)
Source: 国泰君安 191 alpha 研报 (2014), alpha 11."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
    decay_linear,
    delta,
    rank,
    safe_div,
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

__alpha_meta__ = {
    "id": "gtja191_011",
    "theme": ['volume', 'microstructure'],
    "formula_latex": 'SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME,6)',
    "columns_required": ['close', 'high', 'low', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": 'Accumulated money-flow-multiplier × volume over 6 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    mfm = safe_div((c - l) - (h - c), h - l)
    return (mfm * v).rolling(6, min_periods=6).sum()
