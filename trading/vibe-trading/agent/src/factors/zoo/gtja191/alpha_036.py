
# ============================================================
# 中文名称: GTJA #36 - 放量下跌信号
# 简要说明: RANK(DELTA(CORR(HIGH,MEAN(VOLUME,60),5),1)) * (-1*RANK(DELTA(VWAP,1))^3 / RANK(CORR(LOW,MEAN(VOLUME,50),12)))，量价相关变化的组合。
# 典型用途: 多重量价信号的复合反转指标。
# ============================================================
"""GTJA Alpha #36.

Formula: RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP), 6), 2))
Source: 国泰君安 191 alpha 研报 (2014), alpha 36."""

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
    "id": "gtja191_036",
    "theme": ['volume'],
    "formula_latex": 'RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP), 6), 2))',
    "columns_required": ['volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 8,
    "notes": 'Rolling 6d corr summed over 2 days then ranked.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    inner = ts_corr(rank(v), rank(vw), 6)
    return rank(inner.rolling(2, min_periods=2).sum())
