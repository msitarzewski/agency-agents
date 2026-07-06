---
name: pair-trading
description: Pair trading strategy. Trades mean reversion using the spread/ratio Z-score of two correlated instruments. Requires at least two instruments.
category: strategy
---
# Pair Trading Strategy

## Purpose

Select two highly correlated instruments (such as stocks from the same industry or BTC/ETH), monitor how far their price ratio (or spread) deviates from the mean, and trade against extreme deviations while waiting for mean reversion.

## Signal Logic

1. **Compute the price ratio**: `ratio = close_A / close_B`
2. **Rolling mean and standard deviation**: `mean = ratio.rolling(lookback).mean()`, `std = ratio.rolling(lookback).std()`
3. **Z-score**: `z = (ratio - mean) / std`
4. **Signal generation**:
   - Z < -entry_z → long A, short B (ratio is too low, expected to revert)
   - Z > +entry_z → short A, long B (ratio is too high, expected to revert)
   - |Z| < exit_z → close the position (reverted back near the mean)

## Implementation Notes

- Pair trading requires **exactly two instruments** (`codes` array length = 2)
- The first instrument is A (`leg1`), and the second is B (`leg2`)
- Signals for A and B are opposite: when A is long, B is short, and vice versa
- **Equal-weight allocation only**: A and B each take 50% of capital, with no precise hedge-ratio calculation

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| lookback | 60 | Lookback window for mean and standard deviation |
| entry_z | 2.0 | Entry Z-score threshold |
| exit_z | 0.5 | Exit Z-score threshold |

## Example `config.json`

```json
{
  "source": "tushare",
  "codes": ["601318.SH", "601628.SH"],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 1000000,
  "commission": 0.001,
  "extra_fields": null
}
```

Cryptocurrency version:
```json
{
  "source": "okx",
  "codes": ["BTC-USDT", "ETH-USDT"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 1000000,
  "commission": 0.001,
  "extra_fields": null
}
```

## Common Pitfalls

- `codes` must contain exactly 2 instruments, no more and no less
- The date indexes of the two instruments must be aligned (use an inner join), otherwise the ratio calculation will be wrong
- Before the lookback window is filled, Z-scores are `NaN`, so fill signals with 0
- Do not generate same-direction signals for both A and B; pair trading is fundamentally a long-short hedge

## Dependencies

```bash
pip install pandas numpy
```

## Signal Convention

- Instrument A: `0.5` = long, `-0.5` = short, `0` = flat
- Instrument B: direction is opposite to A
