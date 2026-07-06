
# ============================================================
# 中文名称: GTJA #8 - 价格加权均线变化
# 简要说明: RANK(DELTA(((HIGH+LOW)/2)*0.2 + VWAP*0.8, 4)) * -1，加权价格4日变化排名取反。
# 典型用途: 综合价格指标的短期趋势反转信号。
# ============================================================
"""GTJA Alpha #8.

Formula: RANK(DELTA(((HIGH+LOW)/2)*0.2 + VWAP*0.8, 4)) * -1
Source: 国泰君安 191 alpha 研报 (2014), alpha 8."""

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
    "id": "gtja191_008",
    "theme": ['reversal'],
    "formula_latex": 'RANK(DELTA(((HIGH+LOW)/2)*0.2 + VWAP*0.8, 4)) * -1',
    "columns_required": ['high', 'low', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 4,
    "min_warmup_bars": 5,
    "notes": 'Negated rank of 4d change in mid-vwap composite.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    x = ((h + l) / 2.0) * 0.2 + vw * 0.8
    return -1.0 * rank(delta(x, 4))
