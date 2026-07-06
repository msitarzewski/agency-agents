# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量标准差比 10日
# 简要说明: ts_std(volume, 10) / volume，10日成交量变异系数。
# 典型用途: 衡量10日成交量的波动稳定性，值低表示成交量稳定。
# ============================================================
"""qlib158 VSTD10: formula = \\mathrm{ts\\_std}(\\mathrm{volume}, 10) / \\mathrm{volume}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_std

__alpha_meta__ = {
    'id': 'qlib158_vstd10',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\mathrm{ts\\\\_std}(\\\\mathrm{volume}, 10) / \\\\mathrm{volume}',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSTD10 on the supplied OHLCV panel."""
    v = panel['volume']
    return safe_div(ts_std(v, 10), v + 1e-12)
