---
name: seasonal
description: Seasonal/calendar-effect strategy. Generates trading signals from time-based patterns such as month-of-year effects and day-of-week effects. Suitable for any OHLCV data.
category: strategy
---
# Seasonal / Calendar Effect Strategy

## Purpose

Uses time-based regularities in financial markets (month effects, day-of-week effects, and similar patterns) to generate trading signals. Examples include the China A-share "spring rally" (January-March) and the "sell in May" effect.

## Signal Logic

### Month Effect (Default)

- Specified bullish months → go long
- Specified bearish months → go short / stay out
- All other months → stay flat

### Day-of-Week Effect (Optional Overlay)

- Monday / Friday effects
- Start-of-month / end-of-month effects

### Combined Mode

Month signal × weekday signal; open a position only when both confirm.

## Common Calendar Effects Reference

| Effect | Description | Reference Configuration |
|------|------|---------|
| Spring rally | Higher probability of gains in China A-shares from January to March | bullish_months=[1,2,3] |
| Sell in May | Weaker performance from May to October | bearish_months=[5,6,7,8,9,10] |
| Year-end effect | Institutional rebalancing in December | bullish_months=[11,12] |
| Monday effect | Lower returns on Mondays | bearish_weekdays=[0] |
| Friday effect | Higher returns on Fridays | bullish_weekdays=[4] |

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| bullish_months | [1, 2, 3, 11, 12] | Bullish months |
| bearish_months | [5, 6, 7, 8, 9] | Bearish months |
| use_weekday | False | Whether to enable weekday effects |
| bullish_weekdays | [4] | Bullish weekdays (0=Monday, 4=Friday) |
| bearish_weekdays | [0] | Bearish weekdays |

## Common Pitfalls

- `pd.DatetimeIndex.month` starts from 1 (1=January)
- `pd.DatetimeIndex.weekday` starts from 0 (0=Monday, 4=Friday)
- Seasonal strategies are statistical regularities, not deterministic signals, so pay attention to sample size in backtests
- Neutral months (neither in `bullish` nor `bearish`) should output 0 and must not be skipped

## Dependencies

```bash
pip install pandas numpy
```

## Signal Convention

- `1` = long (bullish window), `-1` = short (bearish window), `0` = stand aside
