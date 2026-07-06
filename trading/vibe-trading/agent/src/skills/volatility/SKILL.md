---
name: volatility
description: Volatility strategy. Trades mean reversion based on percentile ranking of historical volatility (HV). Suitable for any OHLCV data.
category: strategy
---
# Volatility Strategy

## Purpose

Uses percentile ranking of historical volatility (HV) to capture volatility mean reversion: build positions in low-volatility regimes while waiting for volatility expansion, and exit or short in high-volatility regimes to capture contraction.

## Signal Logic

1. **Compute HV**: annualized standard deviation of returns over the past `hv_window` days
2. **Percentile ranking**: percentile position of HV within the past `lookback` days (0-100)
3. **Signal generation**:
   - Percentile < `low_pct` → go long (volatility is low, waiting for expansion)
   - Percentile > `high_pct` → exit / go short (volatility is high, waiting for contraction)
   - Middle region → keep the current position

## Key Implementation Details

- HV = `returns.rolling(hv_window).std() * sqrt(252)` (annualized)
- Percentile = `hv.rolling(lookback).rank(pct=True) * 100`
- For cryptocurrencies, use 365 instead of 252 as the annualization factor

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| hv_window | 20 | Historical volatility calculation window |
| lookback | 120 | Lookback period for percentile ranking |
| low_pct | 20.0 | Low-volatility threshold (percentile) |
| high_pct | 80.0 | High-volatility threshold (percentile) |
| annualize | 252 | Annualization factor (252 for China A-shares, 365 for crypto) |

## Common Pitfalls

- Before the lookback window is filled, there is not enough data to compute percentiles, so the signal should be 0 (`fillna`)
- Volatility is not direction. Going long in low-volatility regimes does not guarantee price appreciation; it only means volatility expansion is statistically more likely
- Cryptocurrencies trade 7x24, so `annualize` should be set to 365

## Dependencies

```bash
pip install pandas numpy
```

## Signal Convention

- `1` = long (low-volatility regime), `-1` = short (high-volatility regime), `0` = stand aside
