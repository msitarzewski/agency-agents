# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最大价 60日
# 简要说明: ts_max(high, 60) / close，60日最高价与当前收盘价的比率。
# 典型用途: 衡量当前价格相对于60日最高点的位置，接近1表示接近近期高点。
# ============================================================
"""qlib158 MAX60: formula = \\mathrm{ts\\_max}(\\mathrm{high}, 60) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_max

__alpha_meta__ = {
    'id': 'qlib158_max60',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_max}(\\\\mathrm{high}, 60) / \\\\mathrm{close}',
    'columns_required': ['high', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 MAX60 on the supplied OHLCV panel."""
    h = panel['high']
    c = panel['close']
    return safe_div(ts_max(h, 60), c)
