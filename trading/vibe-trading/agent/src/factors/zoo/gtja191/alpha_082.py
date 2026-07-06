
# ============================================================
# 中文名称: GTJA Alpha #82
# 简要说明: 国泰君安191短周期交易型alpha因子第82号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #82.

Formula: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 82."""

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
    "id": "gtja191_082",
    "theme": ['reversal'],
    "formula_latex": 'SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 21,
    "notes": 'Williams %R with SMA(20,1).',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    hi6 = ts_max(h, 6)
    lo6 = ts_min(l, 6)
    raw = safe_div(hi6 - c, hi6 - lo6) * 100.0
    return raw.ewm(alpha=1.0 / 20.0, adjust=False).mean()
