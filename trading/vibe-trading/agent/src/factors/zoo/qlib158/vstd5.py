# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量标准差比 5日
# 简要说明: ts_std(volume, 5) / volume，5日成交量变异系数。
# 典型用途: 衡量5日成交量的波动稳定性，值低表示成交量稳定。
# ============================================================
"""qlib158 VSTD5: formula = \\mathrm{ts\\_std}(\\mathrm{volume}, 5) / \\mathrm{volume}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_std

__alpha_meta__ = {
    'id': 'qlib158_vstd5',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\mathrm{ts\\\\_std}(\\\\mathrm{volume}, 5) / \\\\mathrm{volume}',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSTD5 on the supplied OHLCV panel."""
    v = panel['volume']
    return safe_div(ts_std(v, 5), v + 1e-12)
