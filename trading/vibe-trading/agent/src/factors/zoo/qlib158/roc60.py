# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 变动率 60日
# 简要说明: close_t / close_{t-60} - 1，60日收益率。
# 典型用途: 经典的60日动量因子，正值为上涨趋势，负值为下跌趋势。
# ============================================================
"""qlib158 ROC60: formula = \\mathrm{close}_t / \\mathrm{close}_{{t-60}} - 1."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_roc60',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{close}_t / \\\\mathrm{close}_{{t-60}} - 1',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 ROC60 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(c, c.shift(60)) - 1.0
