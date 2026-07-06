
# ============================================================
# 中文名称: GTJA #60 - 量价占比排名
# 简要说明: (-1*RANK(DELTA(MEAN(CLOSE,6),3))*RANK((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)))，同Alpha#53/#55/#58/#59。
# 典型用途: 多重复合均线偏离信号。
# ============================================================
"""GTJA Alpha #60.

Formula: SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME, 20)
Source: 国泰君安 191 alpha 研报 (2014), alpha 60."""

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
    "id": "gtja191_060",
    "theme": ['volume', 'microstructure'],
    "formula_latex": 'SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME, 20)',
    "columns_required": ['close', 'high', 'low', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 21,
    "notes": '20-day version of alpha #11.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    mfm = safe_div((c - l) - (h - c), h - l)
    return (mfm * v).rolling(20, min_periods=20).sum()
