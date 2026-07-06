
# ============================================================
# 中文名称: GTJA Alpha #73
# 简要说明: 国泰君安191短周期交易型alpha因子第73号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #73.

Formula: ((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE),VOLUME,10),16),4),5) - RANK(DECAYLINEAR(CORR(VWAP,MEAN(VOLUME,30),4),3))) * -1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 73."""

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
    "id": "gtja191_073",
    "theme": ['volume'],
    "formula_latex": '((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE),VOLUME,10),16),4),5) - RANK(DECAYLINEAR(CORR(VWAP,MEAN(VOLUME,30),4),3))) * -1)',
    "columns_required": ['close', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 16,
    "min_warmup_bars": 35,
    "notes": 'Composite of decay-linear of close-volume corr minus another decay term.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    inner = ts_corr(c, v, 10)
    t1 = ts_rank(decay_linear(decay_linear(inner, 16), 4), 5)
    t2 = rank(decay_linear(ts_corr(vw, ts_mean(v, 30), 4), 3))
    return -1.0 * (t1 - t2)
