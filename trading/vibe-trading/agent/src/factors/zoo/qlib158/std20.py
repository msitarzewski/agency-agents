# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 价格标准差比 20日
# 简要说明: ts_std(close, 20) / close，20日收盘价标准差与收盘价的比率（变异系数）。
# 典型用途: 衡量20日价格波动幅度相对于价格水平的比率，用于波动率排序。
# ============================================================
"""qlib158 STD20: formula = \\mathrm{ts\\_std}(\\mathrm{close}, 20) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_std

__alpha_meta__ = {
    'id': 'qlib158_std20',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_std}(\\\\mathrm{close}, 20) / \\\\mathrm{close}',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 STD20 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(ts_std(c, 20), c)
