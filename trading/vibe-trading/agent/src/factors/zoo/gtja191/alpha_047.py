
# ============================================================
# 中文名称: GTJA #47 - 收益变化乘积
# 简要说明: SMA((CLOSE>DELAY(CLOSE,1)?CLOSE-DELAY(CLOSE,1):0),5,1)/SMA((CLOSE<DELAY(CLOSE,1)?abs(CLOSE-DELAY(CLOSE,1)):0),5,1)*100，上涨变化与下跌变化的比率。
# 典型用途: 价格变化幅度的方向性比率，用于评估多头/空头力度。
# ============================================================
"""GTJA Alpha #47.

Formula: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 47."""

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
    "id": "gtja191_047",
    "theme": ['reversal'],
    "formula_latex": 'SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 9,
    "min_warmup_bars": 10,
    "notes": 'Williams %R style indicator smoothed with SMA(9,1).',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    hi6 = ts_max(h, 6)
    lo6 = ts_min(l, 6)
    raw = safe_div(hi6 - c, hi6 - lo6) * 100.0
    return raw.ewm(alpha=1.0 / 9.0, adjust=False).mean()
