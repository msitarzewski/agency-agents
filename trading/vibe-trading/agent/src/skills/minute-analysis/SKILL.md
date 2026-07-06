---
name: minute-analysis
description: Minute-level data analysis and backtesting. Retrieves minute candlesticks through OKX/Tushare/yfinance and can be used both for analysis and as input to the backtest engine.
category: strategy
---
# Minute-Level Data Analysis and Backtesting

## Purpose

Retrieve minute-level candlestick data through data-source APIs and calculate intraday indicators (VWAP, TWAP, volume distribution, and more).
Supports minute-level backtesting: set `"interval": "5m"` in `config.json` and use the `backtest` tool to run intraday strategies.

## Backtest Configuration

For minute-level backtests, simply add the `interval` field in `config.json`:

```json
{
  "source": "okx",
  "codes": ["BTC-USDT"],
  "start_date": "2026-03-01",
  "end_date": "2026-03-15",
  "interval": "5m",
  "initial_cash": 1000000,
  "commission": 0.0005
}
```

- The annualization factor is inferred automatically from `source + interval` (`OKX 5m = 365 x 288 = 105120`)
- Minute-level datasets are large. Recommended time limits: no more than 7 days for `1m`, no more than 30 days for `5m`, and no more than 1 year for `1H`

## Supported Data Sources and Intervals

| Data Source | Supported Intervals | Notes |
|--------|---------|------|
| OKX | 1m/5m/15m/30m/1H/4H | Cryptocurrency, trades 7x24 |
| Tushare | 1m/5m/15m/30m/1H | China A-shares, requires score >= 2000 |
| yfinance | 1m/5m/15m/30m/1H | Hong Kong / US equities (free, no key required) |

## OKX Minute Candlestick API

```python
import requests
import pandas as pd

resp = requests.get("https://www.okx.com/api/v5/market/candles", params={
    "instId": "BTC-USDT",
    "bar": "1m",       # 1m/5m/15m/30m/1H/4H
    "limit": "300",    # At most 300 rows per request
})
data = resp.json()["data"]
columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"]
df = pd.DataFrame(reversed(data), columns=columns)
df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms")
for col in ["open", "high", "low", "close", "vol"]:
    df[col] = df[col].astype(float)
```

## Indicator Calculation Templates

### VWAP (Volume-Weighted Average Price)

```python
typical_price = (df["high"] + df["low"] + df["close"]) / 3
df["vwap"] = (typical_price * df["vol"]).cumsum() / df["vol"].cumsum()
```

### TWAP (Time-Weighted Average Price)

```python
df["twap"] = df["close"].expanding().mean()
```

### Volume Distribution

```python
df["vol_pct"] = df["vol"] / df["vol"].sum() * 100
hourly_vol = df.set_index("ts").resample("1h")["vol"].sum()
```

## Parameters

| Parameter | Description |
|------|------|
| inst_id | Trading pair, such as `"BTC-USDT"` |
| bar / interval | Candlestick interval: `1m/5m/15m/30m/1H/4H` |
| limit | Number of records to retrieve (OKX returns at most 300 per request) |

## Common Pitfalls

- OKX returns at most 300 rows per request. The loader paginates automatically, but `1m` datasets are still very large
- The time range for minute-level backtests should not be too long, otherwise both data retrieval and backtesting will become slow or time out
- Tushare minute endpoints require a score >= 2000. If the score is insufficient, the API returns empty data
- Timestamps are Unix timestamps in milliseconds and should be converted with `unit="ms"`
- Transaction costs for minute strategies should be set lower (for example 0.05% instead of 0.1%) because intraday trading is frequent

## Dependencies

```bash
pip install pandas numpy requests
```
