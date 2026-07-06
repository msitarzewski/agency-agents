import math
import pandas as pd
import numpy as np

from tradingagents.tools.analysis.indicators import (
    IndicatorSpec,
    compute_many,
)


def make_df(n=60, seed=42):
    rng = np.random.default_rng(seed)
    close = pd.Series(np.cumsum(rng.normal(0, 1, n)) + 100)
    high = close + rng.uniform(0, 2, n)
    low = close - rng.uniform(0, 2, n)
    vol = pd.Series(rng.integers(1000, 5000, n))
    amount = vol * close
    return pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close, 'vol': vol, 'amount': amount
    })


def test_compute_many_basic_columns():
    df = make_df(80)
    specs = [
        IndicatorSpec('ma', {'n': 5}),
        IndicatorSpec('ma', {'n': 20}),
        IndicatorSpec('macd'),
        IndicatorSpec('rsi', {'n': 14}),
        IndicatorSpec('boll', {'n': 20, 'k': 2}),
        IndicatorSpec('atr', {'n': 14}),
        IndicatorSpec('kdj', {'n': 9, 'm1': 3, 'm2': 3}),
    ]
    out = compute_many(df, specs)

    # 列存在
    for col in ['ma5','ma20','dif','dea','macd_hist','rsi14','boll_mid','boll_upper','boll_lower','atr14','kdj_k','kdj_d','kdj_j']:
        assert col in out.columns

    # 最后一行应有数值（对应窗口已满足）
    last = out.iloc[-1]
    for col in ['ma5','ma20','dif','dea','macd_hist','rsi14','boll_mid','boll_upper','boll_lower','atr14','kdj_k','kdj_d','kdj_j']:
        assert not pd.isna(last[col]), f"{col} should not be NaN"


def test_no_inplace_modification():
    df = make_df(40)
    out = compute_many(df, [IndicatorSpec('ma', {'n': 5})])
    assert 'ma5' in out.columns and 'ma5' not in df.columns

