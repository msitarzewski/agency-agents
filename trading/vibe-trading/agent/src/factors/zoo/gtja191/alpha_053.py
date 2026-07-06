
# ============================================================
# 中文名称: GTJA #53 - 高低价差比
# 简要说明: (-1*RANK(DELTA(MEAN(CLOSE,6),3))*RANK((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)))，均值变化与偏离度的组合。
# 典型用途: 均线趋势变化与当前偏离度的综合信号。
# ============================================================
"""GTJA Alpha #53.

Formula: COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100
Source: 国泰君安 191 alpha 研报 (2014), alpha 53."""

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
    "id": "gtja191_053",
    "theme": ['momentum'],
    "formula_latex": 'COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 12,
    "min_warmup_bars": 13,
    "notes": 'Pct of up-days in 12d window.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    up = (c > c.shift(1)).astype(float)
    return up.rolling(12, min_periods=12).sum() / 12.0 * 100.0
