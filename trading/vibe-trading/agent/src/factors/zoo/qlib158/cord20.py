# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 收益率-量变化相关性 20日
# 简要说明: ts_corr(close/close_prev, log(v/v_prev), 20)，20日收益率与成交量变化率的相关系数。
# 典型用途: 衡量20日价格变动与成交量变动的相关性，反映量价配合程度。
# ============================================================
"""qlib158 CORD20: formula = \\mathrm{ts\\_corr}(\\mathrm{close}/\\mathrm{close}_{{-1}}, \\log((\\mathrm{volume}+1)/(\\mathrm{volume}_{{-1}}+1)), 20)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from src.factors.base import safe_div, ts_corr

__alpha_meta__ = {
    'id': 'qlib158_cord20',
    'theme': ['volume', 'microstructure'],
    'formula_latex': '\\\\mathrm{ts\\\\_corr}(\\\\mathrm{close}/\\\\mathrm{close}_{{-1}}, \\\\log((\\\\mathrm{volume}+1)/(\\\\mathrm{volume}_{{-1}}+1)), 20)',
    'columns_required': ['close', 'volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CORD20 on the supplied OHLCV panel."""
    c = panel['close']
    v = panel['volume']
    c_ret = safe_div(c, c.shift(1))
    v_ret = safe_div(v + 1.0, v.shift(1) + 1.0)
    logvr = np.log(v_ret)
    return ts_corr(c_ret, logvr, 20)
