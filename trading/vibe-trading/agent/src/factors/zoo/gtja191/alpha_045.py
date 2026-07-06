
# ============================================================
# 中文名称: GTJA #45 - 加权平均变化
# 简要说明: (RANK(DELTA((((CLOSE*0.6)+(OPEN*0.4))),1)) * RANK(CORR(VWAP,MEAN(VOLUME,150),15)))，加权价格的1日变化与长期量价相关的乘积。
# 典型用途: 短期价格变化与长期量价模式的匹配信号。
# ============================================================
"""GTJA Alpha #45.

Formula: (RANK(DELTA((((CLOSE*0.6)+(OPEN*0.4))),1)) * RANK(CORR(VWAP,MEAN(VOLUME,150),15)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 45."""

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
    "id": "gtja191_045",
    "theme": ['volume'],
    "formula_latex": '(RANK(DELTA((((CLOSE*0.6)+(OPEN*0.4))),1)) * RANK(CORR(VWAP,MEAN(VOLUME,150),15)))',
    "columns_required": ['close', 'open', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 15,
    "min_warmup_bars": 44,
    "notes": '150d MA volume approximated with 30d window.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    o = panel["open"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    blend = c * 0.6 + o * 0.4
    return rank(delta(blend, 1)) * rank(ts_corr(vw, ts_mean(v, 30), 15))
