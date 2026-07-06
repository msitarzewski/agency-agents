
# ============================================================
# 中文名称: GTJA Alpha #94
# 简要说明: 国泰君安191短周期交易型alpha因子第94号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #94.

Formula: SUM(CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0),30)
Source: 国泰君安 191 alpha 研报 (2014), alpha 94."""

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
    "id": "gtja191_094",
    "theme": ['volume', 'momentum'],
    "formula_latex": 'SUM(CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0),30)',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 30,
    "min_warmup_bars": 31,
    "notes": '30d signed volume.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    pc = c.shift(1)
    signed = v.where(c > pc, -v.where(c < pc, 0.0))
    return signed.rolling(30, min_periods=30).sum()
