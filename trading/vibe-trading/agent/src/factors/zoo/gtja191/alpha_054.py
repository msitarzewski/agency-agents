
# ============================================================
# 中文名称: GTJA #54 - 量价同步
# 简要说明: (-1*RANK((CLOSE-OPEN)/OPEN)*RANK(CORR(HIGH,MEAN(VOLUME,20),5)))，日内收益与量价相关的组合取反。
# 典型用途: 日内价格变动与量价关系的交叉验证信号。
# ============================================================
"""GTJA Alpha #54.

Formula: ((-1*RANK((STD(ABS(CLOSE-OPEN),10)+(CLOSE-OPEN))+CORR(CLOSE,OPEN,10))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 54."""

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
    "id": "gtja191_054",
    "theme": ['volatility', 'microstructure'],
    "formula_latex": '((-1*RANK((STD(ABS(CLOSE-OPEN),10)+(CLOSE-OPEN))+CORR(CLOSE,OPEN,10))))',
    "columns_required": ['close', 'open'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 10,
    "min_warmup_bars": 11,
    "notes": 'Negated rank of (std|c-o|,10) + (c-o) + corr(c,o,10).',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    o = panel["open"]
    return -1.0 * rank(ts_std((c - o).abs(), 10) + (c - o) + ts_corr(c, o, 10))
