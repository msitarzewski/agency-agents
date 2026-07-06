
# ============================================================
# 中文名称: GTJA Alpha #75
# 简要说明: 国泰君安191短周期交易型alpha因子第75号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #75.

Formula: COUNT((CLOSE>OPEN & BENCHMARKINDEXCLOSE<DELAY(BENCHMARKINDEXCLOSE,1)),50)/COUNT(BENCHMARKINDEXCLOSE<DELAY(BENCHMARKINDEXCLOSE,1),50)
Source: 国泰君安 191 alpha 研报 (2014), alpha 75."""

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
    "id": "gtja191_075",
    "theme": ['sentiment', 'momentum'],
    "formula_latex": 'COUNT((CLOSE>OPEN & BENCHMARKINDEXCLOSE<DELAY(BENCHMARKINDEXCLOSE,1)),50)/COUNT(BENCHMARKINDEXCLOSE<DELAY(BENCHMARKINDEXCLOSE,1),50)',
    "columns_required": ['close', 'open'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 50,
    "min_warmup_bars": 30,
    "notes": 'Benchmark unavailable in zoo panel; degraded to row-mean(close) as benchmark proxy. Window 50→20. See notes.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    o = panel["open"]
    bench_row = c.mean(axis=1).to_numpy(dtype=float)
    bench_df = pd.DataFrame(np.broadcast_to(bench_row[:, None], c.shape).copy(),
                            index=c.index, columns=c.columns)
    bench_down = (bench_df < bench_df.shift(1)).astype(float)
    up_and_down = ((c > o) & (bench_df < bench_df.shift(1))).astype(float)
    num = up_and_down.rolling(20, min_periods=20).sum()
    den = bench_down.rolling(20, min_periods=20).sum()
    return safe_div(num, den)
