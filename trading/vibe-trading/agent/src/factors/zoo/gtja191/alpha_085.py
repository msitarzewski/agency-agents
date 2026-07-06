
# ============================================================
# 中文名称: GTJA Alpha #85
# 简要说明: 国泰君安191短周期交易型alpha因子第85号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #85.

Formula: (TSRANK((VOLUME/MEAN(VOLUME,20)),20)*TSRANK((-1*DELTA(CLOSE,7)),8))
Source: 国泰君安 191 alpha 研报 (2014), alpha 85."""

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
    "id": "gtja191_085",
    "theme": ['volume', 'momentum'],
    "formula_latex": '(TSRANK((VOLUME/MEAN(VOLUME,20)),20)*TSRANK((-1*DELTA(CLOSE,7)),8))',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 39,
    "notes": 'Vol-adjusted contrarian momentum.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    c = panel["close"]
    vol_ratio = safe_div(v, ts_mean(v, 20))
    return ts_rank(vol_ratio, 20) * ts_rank(-1.0 * delta(c, 7), 8)
