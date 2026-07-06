
# ============================================================
# 中文名称: GTJA Alpha #63
# 简要说明: 国泰君安191短周期交易型alpha因子第63号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #63.

Formula: SMA(MAX(CLOSE-DELAY(CLOSE,1),0),6,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),6,1)*100
Source: 国泰君安 191 alpha 研报 (2014), alpha 63."""

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
    "id": "gtja191_063",
    "theme": ['momentum'],
    "formula_latex": 'SMA(MAX(CLOSE-DELAY(CLOSE,1),0),6,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),6,1)*100',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": 'RSI-6 style.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    diff = c - c.shift(1)
    up_part = diff.clip(lower=0)
    abs_part = diff.abs()
    u = up_part.ewm(alpha=1.0 / 6.0, adjust=False).mean()
    a = abs_part.ewm(alpha=1.0 / 6.0, adjust=False).mean()
    return safe_div(u, a) * 100.0
