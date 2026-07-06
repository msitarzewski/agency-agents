# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 上涨天数计数 30日
# 简要说明: rolling_mean(1[close>close_prev], 30)，30日内上涨天数占比。
# 典型用途: 衡量30日内上涨频率，值高表示持续上涨行情。
# ============================================================
"""qlib158 CNTP30: formula = \\mathrm{rolling\\_mean}(\\mathrm{1}[\\mathrm{close}>\\mathrm{close}_{{-1}}], 30)."""
from __future__ import annotations

import pandas as pd

__alpha_meta__ = {
    'id': 'qlib158_cntp30',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{rolling\\\\_mean}(\\\\mathrm{1}[\\\\mathrm{close}>\\\\mathrm{close}_{{-1}}], 30)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CNTP30 on the supplied OHLCV panel."""
    c = panel['close']
    up = (c > c.shift(1)).astype('float64')
    return up.rolling(window=30, min_periods=30).mean()
