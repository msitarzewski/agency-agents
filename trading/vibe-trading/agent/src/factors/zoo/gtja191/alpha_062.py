
# ============================================================
# 中文名称: GTJA Alpha #62
# 简要说明: 国泰君安191短周期交易型alpha因子第62号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #62.

Formula: ((-1*CORR(HIGH,RANK(VOLUME),5)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 62."""

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
    "id": "gtja191_062",
    "theme": ['volume'],
    "formula_latex": '((-1*CORR(HIGH,RANK(VOLUME),5)))',
    "columns_required": ['high', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": 'Negated 5d corr(high, rank(volume)).',
}

def compute(panel: dict) -> pd.DataFrame:
    return -1.0 * ts_corr(panel["high"], rank(panel["volume"]), 5)
