
# ============================================================
# 中文名称: GTJA Alpha #68
# 简要说明: 国泰君安191短周期交易型alpha因子第68号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #68.

Formula: SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)
Source: 国泰君安 191 alpha 研报 (2014), alpha 68."""

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
    "id": "gtja191_068",
    "theme": ['volume'],
    "formula_latex": 'SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)',
    "columns_required": ['high', 'low', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 15,
    "min_warmup_bars": 16,
    "notes": 'Like alpha #9 but with SMA(15, m=2).',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    mid = (h + l) / 2.0
    pmid = (h.shift(1) + l.shift(1)) / 2.0
    x = (mid - pmid) * safe_div(h - l, v)
    return x.ewm(alpha=2.0 / 15.0, adjust=False).mean()
