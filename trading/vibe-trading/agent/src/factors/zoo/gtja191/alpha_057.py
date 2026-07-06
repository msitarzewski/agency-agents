
# ============================================================
# 中文名称: GTJA #57 - 量价关系二阶
# 简要说明: SMA((CLOSE>DELAY(CLOSE,1)?CLOSE-DELAY(CLOSE,1):0),5,1)/SMA((CLOSE<DELAY(CLOSE,1)?abs(CLOSE-DELAY(CLOSE,1)):0),5,1)*100，同Alpha#47。
# 典型用途: 上涨与下跌幅度的比率，用于评估短期多空力度。
# ============================================================
"""GTJA Alpha #57.

Formula: SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 57."""

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
    "id": "gtja191_057",
    "theme": ['momentum'],
    "formula_latex": 'SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 9,
    "min_warmup_bars": 10,
    "notes": 'KDJ %K-style indicator with SMA(3,1) smoothing.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    lo9 = ts_min(l, 9)
    hi9 = ts_max(h, 9)
    raw = safe_div(c - lo9, hi9 - lo9) * 100.0
    return raw.ewm(alpha=1.0 / 3.0, adjust=False).mean()
