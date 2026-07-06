---
name: technical-basic
description: Core technical indicator collection (trend EMA/ADX + mean-reversion BB/RSI + volume-price OBV/volume ratio), generates a composite signal via three-dimensional voting. Pure pandas implementation for any OHLCV data.
category: strategy
---
# Core Technical Indicator Collection

## Purpose

Combines three classic Western technical analysis approaches into one composite signal engine:

| Dimension | Indicators | Purpose |
|------|------|------|
| Trend | EMA(12/26) + ADX(14) | Determine direction and trend strength |
| Mean reversion | Bollinger Bands(20,2) + RSI(14) | Detect overbought and oversold conditions |
| Volume-price | OBV + volume ratio | Confirm volume participation |

## Signal Logic

Three-dimensional voting mechanism:
- **Long**: trend is bullish + RSI is not overbought + OBV is rising
- **Short**: trend is bearish + RSI is not oversold + OBV is falling
- **Stand aside**: mixed signals

## Key Implementation Details

- RSI and ADX use **Wilder EWM** (`ewm(alpha=1/period)`), not a rolling mean
- Full ADX chain: +DM/-DM → TR → +DI/-DI → DX → ADX
- OBV = `(volume * sign(close.diff())).cumsum()`

## Parameters

All parameters have default values and can be overridden at instantiation time:

| Parameter | Default | Description |
|------|--------|------|
| ema_fast | 12 | Fast EMA period |
| ema_slow | 26 | Slow EMA period |
| adx_period | 14 | ADX calculation period |
| adx_threshold | 25.0 | ADX trend-strength threshold |
| bb_window | 20 | Bollinger Band window |
| bb_std | 2.0 | Bollinger Band standard deviation multiplier |
| rsi_period | 14 | RSI period |
| rsi_oversold | 30 | RSI oversold threshold |
| rsi_overbought | 70 | RSI overbought threshold |
| vol_ma_period | 20 | Volume moving-average period |
| obv_ma_period | 20 | OBV moving-average period |

## Dependencies

```bash
pip install pandas numpy requests
```

## Signal Convention

- `1` = long, `-1` = short, `0` = stand aside
