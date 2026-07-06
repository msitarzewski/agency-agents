
# ============================================================
# 中文名称: GTJA #28 - 量价加速度
# 简要说明: (-1*RANK(DELTA(CORR(HIGH,MEAN(VOLUME,60),5),1))*RANK(CORR(CLOSE,MEAN(VOLUME,50),1)))，量价相关性变化与当前相关性的乘积。
# 典型用途: 量价关系的加速度指标，变化加速预示趋势加强。
# ============================================================
"""GTJA Alpha #28.

Formula: 3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 28."""

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
    "id": "gtja191_028",
    "theme": ['momentum'],
    "formula_latex": '3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 9,
    "min_warmup_bars": 12,
    "notes": 'Stochastic-like indicator double-smoothed.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    lo9 = ts_min(l, 9)
    hi9 = ts_max(h, 9)
    raw = safe_div(c - lo9, hi9 - lo9) * 100.0
    s1 = raw.ewm(alpha=1.0 / 3.0, adjust=False).mean()
    s2 = s1.ewm(alpha=1.0 / 3.0, adjust=False).mean()
    return 3.0 * s1 - 2.0 * s2
