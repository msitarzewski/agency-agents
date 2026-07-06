# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 时间序列排名 30日
# 简要说明: ts_rank(close, 30)，当前收盘价在30日窗口内的百分位排名。
# 典型用途: 衡量当前价格在过去30日中的相对位置，高排名表示处于近期高位。
# ============================================================
"""qlib158 RANK30: formula = \\mathrm{ts\\_rank}(\\mathrm{close}, 30)."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_rank, rank

__alpha_meta__ = {
    'id': 'qlib158_rank30',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_rank}(\\\\mathrm{close}, 30)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 RANK30 on the supplied OHLCV panel."""
    c = panel['close']
    return ts_rank(c, 30)
