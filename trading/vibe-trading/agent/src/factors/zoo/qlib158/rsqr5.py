# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: R平方 5日
# 简要说明: ts_corr(close, t, 5)^2，收盘价对时间的5日线性回归拟合度。
# 典型用途: 衡量5日价格趋势的线性强度，值高表示趋势明确。
# ============================================================
"""qlib158 RSQR5: formula = \\mathrm{ts\\_corr}(\\mathrm{close}, t, 5)^2."""
from __future__ import annotations

import numpy as np
import pandas as pd
from src.factors.base import ts_corr

__alpha_meta__ = {
    'id': 'qlib158_rsqr5',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_corr}(\\\\mathrm{close}, t, 5)^2',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 RSQR5 on the supplied OHLCV panel."""
    c = panel['close']
    t_arr = np.arange(len(c.index), dtype=np.float64)
    t_df = pd.DataFrame(np.broadcast_to(t_arr[:, None], c.shape).copy(), index=c.index, columns=c.columns)
    corr = ts_corr(c, t_df, 5)
    return corr * corr
