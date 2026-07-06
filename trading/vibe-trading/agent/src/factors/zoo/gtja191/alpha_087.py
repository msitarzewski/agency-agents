
# ============================================================
# 中文名称: GTJA Alpha #87
# 简要说明: 国泰君安191短周期交易型alpha因子第87号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #87.

Formula: ((RANK(DECAYLINEAR(DELTA(VWAP,4),7))+TSRANK(DECAYLINEAR((((LOW*0.9)+(LOW*0.1))-VWAP)/(OPEN-((HIGH+LOW)/2)),11),7))*-1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 87."""

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
    "id": "gtja191_087",
    "theme": ['microstructure'],
    "formula_latex": '((RANK(DECAYLINEAR(DELTA(VWAP,4),7))+TSRANK(DECAYLINEAR((((LOW*0.9)+(LOW*0.1))-VWAP)/(OPEN-((HIGH+LOW)/2)),11),7))*-1)',
    "columns_required": ['close', 'open', 'high', 'low', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 11,
    "min_warmup_bars": 22,
    "notes": 'Sum of two decay-linear terms, negated.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    p1 = rank(decay_linear(delta(vw, 4), 7))
    numer = (l * 0.9 + l * 0.1) - vw
    denom = o - (h + l) / 2.0
    p2 = ts_rank(decay_linear(safe_div(numer, denom), 11), 7)
    return -1.0 * (p1 + p2)
