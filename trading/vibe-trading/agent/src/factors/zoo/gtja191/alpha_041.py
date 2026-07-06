
# ============================================================
# 中文名称: GTJA #41 - VWAP标准差
# 简要说明: RANK(MAX(DELTA(VWAP,1),3))*RANK(DELTA(VOLUME,3))，VWAP与成交量3日变化的极值排名乘积。
# 典型用途: VWAP变化与成交量变化的组合信号。
# ============================================================
"""GTJA Alpha #41.

Formula: (RANK(MAX(DELTA(VWAP,3),5))*-1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 41."""

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
    "id": "gtja191_041",
    "theme": ['microstructure'],
    "formula_latex": '(RANK(MAX(DELTA(VWAP,3),5))*-1)',
    "columns_required": ['volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 9,
    "notes": '5d max of 3d delta(vwap), ranked, negated.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    return -1.0 * rank(ts_max(delta(vw, 3), 5))
