
# ============================================================
# 中文名称: GTJA #37 - 开盘累计变化
# 简要说明: (-1*RANK(((SUM(OPEN,5)*SUM(RET,5))-DELAY((SUM(OPEN,5)*SUM(RET,5)),10))))，开盘累计与收益累计的10日滞后差排名。
# 典型用途: 开盘价与收益率累计变化的速度差异，用于趋势加速/减速判断。
# ============================================================
"""GTJA Alpha #37.

Formula: (-1*RANK(((SUM(OPEN,5)*SUM(RET,5))-DELAY((SUM(OPEN,5)*SUM(RET,5)),10))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 37."""

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
    "id": "gtja191_037",
    "theme": ['momentum'],
    "formula_latex": '(-1*RANK(((SUM(OPEN,5)*SUM(RET,5))-DELAY((SUM(OPEN,5)*SUM(RET,5)),10))))',
    "columns_required": ['open', 'close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 10,
    "min_warmup_bars": 16,
    "notes": 'Change over 10d of product (sum(open,5)*sum(ret,5)).',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    c = panel["close"]
    pc = c.shift(1)
    ret = safe_div(c - pc, pc)
    prod = o.rolling(5, min_periods=5).sum() * ret.rolling(5, min_periods=5).sum()
    return -1.0 * rank(prod - prod.shift(10))
