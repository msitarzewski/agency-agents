# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 下跌天数计数 60日
# 简要说明: rolling_mean(1[close<close_prev], 60)，60日内下跌天数占比。
# 典型用途: 衡量60日内下跌频率，值高表示持续下跌行情。
# ============================================================
"""qlib158 CNTN60: formula = \\mathrm{rolling\\_mean}(\\mathrm{1}[\\mathrm{close}<\\mathrm{close}_{{-1}}], 60)."""
from __future__ import annotations

import pandas as pd

__alpha_meta__ = {
    'id': 'qlib158_cntn60',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{rolling\\\\_mean}(\\\\mathrm{1}[\\\\mathrm{close}<\\\\mathrm{close}_{{-1}}], 60)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CNTN60 on the supplied OHLCV panel."""
    c = panel['close']
    dn = (c < c.shift(1)).astype('float64')
    return dn.rolling(window=60, min_periods=60).mean()
