
# ============================================================
# 中文名称: GTJA Alpha #74
# 简要说明: 国泰君安191短周期交易型alpha因子第74号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #74.

Formula: (RANK(CORR(SUM(((LOW*0.35)+(VWAP*0.65)),20),SUM(MEAN(VOLUME,40),20),7)) + RANK(CORR(RANK(VWAP),RANK(VOLUME),6)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 74."""

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
    "id": "gtja191_074",
    "theme": ['volume'],
    "formula_latex": '(RANK(CORR(SUM(((LOW*0.35)+(VWAP*0.65)),20),SUM(MEAN(VOLUME,40),20),7)) + RANK(CORR(RANK(VWAP),RANK(VOLUME),6)))',
    "columns_required": ['low', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 30,
    "notes": '40d MA volume truncated to 10d; SUM windows kept at 20.',
}

def compute(panel: dict) -> pd.DataFrame:
    l = panel["low"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    sumA = (l * 0.35 + vw * 0.65).rolling(10, min_periods=10).sum()
    sumB = ts_mean(v, 10).rolling(10, min_periods=10).sum()
    t1 = rank(ts_corr(sumA, sumB, 7))
    t2 = rank(ts_corr(rank(vw), rank(v), 6))
    return t1 + t2
