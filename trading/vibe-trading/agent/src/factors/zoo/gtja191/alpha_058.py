
# ============================================================
# 中文名称: GTJA #58 - 均线偏离度
# 简要说明: (-1*RANK(DELTA(MEAN(CLOSE,6),3))*RANK((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)))，类似Alpha#53/#55。
# 典型用途: 均线变化与偏离度的反转组合信号。
# ============================================================
"""GTJA Alpha #58.

Formula: COUNT(CLOSE>DELAY(CLOSE,1),20)/20*100
Source: 国泰君安 191 alpha 研报 (2014), alpha 58."""

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
    "id": "gtja191_058",
    "theme": ['momentum'],
    "formula_latex": 'COUNT(CLOSE>DELAY(CLOSE,1),20)/20*100',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 21,
    "notes": 'Pct of up-days in 20d window.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    up = (c > c.shift(1)).astype(float)
    return up.rolling(20, min_periods=20).sum() / 20.0 * 100.0
