
# ============================================================
# 中文名称: GTJA #7 - VWAP相对强度
# 简要说明: ((RANK(MAX((VWAP-CLOSE), 3)) + RANK(MIN((VWAP-CLOSE), 3))) * RANK(DELTA(VOLUME, 3)))，VWAP偏离的极值与成交量变化的组合。
# 典型用途: 综合考虑VWAP偏离幅度和成交量变化，识别潜在的突破或反转。
# ============================================================
"""GTJA Alpha #7.

Formula: ((RANK(MAX((VWAP-CLOSE),3)) + RANK(MIN((VWAP-CLOSE),3))) * RANK(DELTA(VOLUME,3)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 7."""

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
    "id": "gtja191_007",
    "theme": ['volume', 'microstructure'],
    "formula_latex": '((RANK(MAX((VWAP-CLOSE),3)) + RANK(MIN((VWAP-CLOSE),3))) * RANK(DELTA(VOLUME,3)))',
    "columns_required": ['close', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 3,
    "min_warmup_bars": 4,
    "notes": 'VWAP via A-share amount/volume (equity_cn convention).',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    c = panel["close"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    diff = vw - c
    return (rank(ts_max(diff, 3)) + rank(ts_min(diff, 3))) * rank(delta(v, 3))
