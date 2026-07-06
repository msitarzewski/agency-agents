
# ============================================================
# 中文名称: GTJA Alpha #99
# 简要说明: 国泰君安191短周期交易型alpha因子第99号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #99.

Formula: (-1*RANK(COVIANCE(RANK(CLOSE),RANK(VOLUME),5)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 99."""

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
    "id": "gtja191_099",
    "theme": ['volume'],
    "formula_latex": '(-1*RANK(COVIANCE(RANK(CLOSE),RANK(VOLUME),5)))',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": 'Negated rank of 5d cov(rank close, rank volume).',
}

def compute(panel: dict) -> pd.DataFrame:
    return -1.0 * rank(ts_cov(rank(panel["close"]), rank(panel["volume"]), 5))
