
# ============================================================
# 中文名称: GTJA Alpha #78
# 简要说明: 国泰君安191短周期交易型alpha因子第78号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #78.

Formula: ((HIGH+LOW+CLOSE)/3-MA((HIGH+LOW+CLOSE)/3,12))/(0.015*MEAN(ABS(CLOSE-MA((HIGH+LOW+CLOSE)/3,12)),12))
Source: 国泰君安 191 alpha 研报 (2014), alpha 78."""

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
    "id": "gtja191_078",
    "theme": ['reversal'],
    "formula_latex": '((HIGH+LOW+CLOSE)/3-MA((HIGH+LOW+CLOSE)/3,12))/(0.015*MEAN(ABS(CLOSE-MA((HIGH+LOW+CLOSE)/3,12)),12))',
    "columns_required": ['high', 'low', 'close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 12,
    "min_warmup_bars": 23,
    "notes": 'CCI-12 style.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    c = panel["close"]
    typ = (h + l + c) / 3.0
    ma = ts_mean(typ, 12)
    md = ts_mean((c - ma).abs(), 12)
    return safe_div(typ - ma, 0.015 * md)
