# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 变动率 20日
# 简要说明: close_t / close_{t-20} - 1，20日收益率。
# 典型用途: 经典的20日动量因子，正值为上涨趋势，负值为下跌趋势。
# ============================================================
"""qlib158 ROC20: formula = \\mathrm{close}_t / \\mathrm{close}_{{t-20}} - 1."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_roc20',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{close}_t / \\\\mathrm{close}_{{t-20}} - 1',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 ROC20 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(c, c.shift(20)) - 1.0
