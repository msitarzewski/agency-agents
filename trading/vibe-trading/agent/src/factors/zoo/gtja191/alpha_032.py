
# ============================================================
# 中文名称: GTJA #32 - 高低价差比
# 简要说明: (-1*RANK(DELTA(VWAP,1))^3 / RANK(CORR(LOW,MEAN(VOLUME,50),12)))，类似Alpha#31的不同实现。
# 典型用途: 识别VWAP变化过快时的回归机会。
# ============================================================
"""GTJA Alpha #32.

Formula: (-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))
Source: 国泰君安 191 alpha 研报 (2014), alpha 32."""

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
    "id": "gtja191_032",
    "theme": ['volume'],
    "formula_latex": '(-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))',
    "columns_required": ['high', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 3,
    "min_warmup_bars": 7,
    "notes": 'Negated 3d sum of rank-corr(rank(high), rank(volume), 3).',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    v = panel["volume"]
    inner = rank(ts_corr(rank(h), rank(v), 3))
    return -1.0 * inner.rolling(3, min_periods=3).sum()
