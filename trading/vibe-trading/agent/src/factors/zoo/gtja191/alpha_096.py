
# ============================================================
# 中文名称: GTJA Alpha #96
# 简要说明: 国泰君安191短周期交易型alpha因子第96号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #96.

Formula: SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 96."""

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
    "id": "gtja191_096",
    "theme": ['momentum'],
    "formula_latex": 'SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 9,
    "min_warmup_bars": 12,
    "notes": 'KDJ %D-style double smoothed.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    raw = safe_div(c - ts_min(l, 9), ts_max(h, 9) - ts_min(l, 9)) * 100.0
    return raw.ewm(alpha=1.0 / 3.0, adjust=False).mean().ewm(alpha=1.0 / 3.0, adjust=False).mean()
