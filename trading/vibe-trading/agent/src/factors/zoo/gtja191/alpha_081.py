
# ============================================================
# 中文名称: GTJA Alpha #81
# 简要说明: 国泰君安191短周期交易型alpha因子第81号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #81.

Formula: SMA(VOLUME,21,2)
Source: 国泰君安 191 alpha 研报 (2014), alpha 81."""

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
    "id": "gtja191_081",
    "theme": ['volume'],
    "formula_latex": 'SMA(VOLUME,21,2)',
    "columns_required": ['volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 21,
    "min_warmup_bars": 22,
    "notes": 'SMA(21, m=2) of volume.',
}

def compute(panel: dict) -> pd.DataFrame:
    return panel["volume"].ewm(alpha=2.0 / 21.0, adjust=False).mean()
