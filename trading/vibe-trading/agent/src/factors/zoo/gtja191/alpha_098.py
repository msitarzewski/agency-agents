
# ============================================================
# 中文名称: GTJA Alpha #98
# 简要说明: 国泰君安191短周期交易型alpha因子第98号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #98.

Formula: ((((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))<0.05) || ((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))==0.05)) ? (-1*(CLOSE-TSMIN(CLOSE,100))) : (-1*DELTA(CLOSE,3)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 98."""

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
    "id": "gtja191_098",
    "theme": ['reversal'],
    "formula_latex": '((((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))<0.05) || ((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))==0.05)) ? (-1*(CLOSE-TSMIN(CLOSE,100))) : (-1*DELTA(CLOSE,3)))',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 30,
    "min_warmup_bars": 60,
    "notes": '100d windows truncated to 30d for warmup feasibility.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    ma = ts_mean(c, 30)
    cond_a = safe_div(delta(ma, 30), c.shift(30)) <= 0.05
    branch1 = -1.0 * (c - ts_min(c, 30))
    branch2 = -1.0 * delta(c, 3)
    return branch1.where(cond_a, branch2)
