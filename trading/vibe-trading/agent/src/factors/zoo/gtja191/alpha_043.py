
# ============================================================
# 中文名称: GTJA #43 - 收益递归平均
# 简要说明: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:0),26)/SUM((CLOSE<=DELAY(CLOSE,1)?VOLUME:0),26)*100，类似Alpha#40的变种。
# 典型用途: 上涨量与下跌量的比值，用于评估市场参与者的方向偏好。
# ============================================================
"""GTJA Alpha #43.

Formula: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),6)
Source: 国泰君安 191 alpha 研报 (2014), alpha 43."""

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
    "id": "gtja191_043",
    "theme": ['volume', 'momentum'],
    "formula_latex": 'SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),6)',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": 'Signed volume accumulation over 6 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    pc = c.shift(1)
    signed = v.where(c > pc, -v.where(c < pc, 0.0))
    return signed.rolling(6, min_periods=6).sum()
