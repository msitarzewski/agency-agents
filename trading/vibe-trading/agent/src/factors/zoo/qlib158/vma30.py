# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量均线比 30日
# 简要说明: ts_mean(volume, 30) / volume，30日平均成交量与当日成交量的比率。
# 典型用途: 判断当日成交量的相对大小，大于1表示缩量，小于1表示放量。
# ============================================================
"""qlib158 VMA30: formula = \\mathrm{ts\\_mean}(\\mathrm{volume}, 30) / \\mathrm{volume}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_mean

__alpha_meta__ = {
    'id': 'qlib158_vma30',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\mathrm{ts\\\\_mean}(\\\\mathrm{volume}, 30) / \\\\mathrm{volume}',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VMA30 on the supplied OHLCV panel."""
    v = panel['volume']
    return safe_div(ts_mean(v, 30), v + 1e-12)
