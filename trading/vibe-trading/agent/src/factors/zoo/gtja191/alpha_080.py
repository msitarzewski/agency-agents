
# ============================================================
# 中文名称: GTJA Alpha #80
# 简要说明: 国泰君安191短周期交易型alpha因子第80号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #80.

Formula: (VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100
Source: 国泰君安 191 alpha 研报 (2014), alpha 80."""

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
    "id": "gtja191_080",
    "theme": ['volume'],
    "formula_latex": '(VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100',
    "columns_required": ['volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": '5d volume change pct.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    pv = v.shift(5)
    return safe_div(v - pv, pv) * 100.0
