# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 变动率 30日
# 简要说明: close_t / close_{t-30} - 1，30日收益率。
# 典型用途: 经典的30日动量因子，正值为上涨趋势，负值为下跌趋势。
# ============================================================
"""qlib158 ROC30: formula = \\mathrm{close}_t / \\mathrm{close}_{{t-30}} - 1."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_roc30',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{close}_t / \\\\mathrm{close}_{{t-30}} - 1',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 ROC30 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(c, c.shift(30)) - 1.0
