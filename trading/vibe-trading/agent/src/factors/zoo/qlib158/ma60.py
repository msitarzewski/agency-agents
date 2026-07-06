# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 移动均线比 60日
# 简要说明: ts_mean(close, 60) / close，60日简单移动平均与收盘价的比率。
# 典型用途: 价格相对于均线的位置，大于1表示价格在均线上方，用于趋势判断。
# ============================================================
"""qlib158 MA60: formula = \\mathrm{ts\\_mean}(\\mathrm{close}, 60) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_mean

__alpha_meta__ = {
    'id': 'qlib158_ma60',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_mean}(\\\\mathrm{close}, 60) / \\\\mathrm{close}',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 MA60 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(ts_mean(c, 60), c)
