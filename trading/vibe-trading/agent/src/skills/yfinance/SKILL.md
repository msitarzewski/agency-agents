---
name: yfinance
description: yfinance global market data interface — retrieve OHLCV, financials, insider transactions, and institutional holdings for US stocks, HK stocks, ETFs, and indices via Yahoo Finance. Free, no API key required.
category: data-source
---
# yfinance

## Overview

yfinance is an open-source Python wrapper for Yahoo Finance, providing global market data (US stocks, HK stocks, ETFs, indices) including historical and real-time quotes. **Completely free, no registration or API key required.**

The project has a built-in yfinance DataLoader (`backtest/loaders/yfinance_loader.py`). When backtesting, set `source: "yfinance"` or `source: "auto"` to invoke it automatically.

For OHLCV bars in agent/swarm work, prefer the `get_market_data` tool when it is available. It routes through the project loader layer, normalizes symbols, removes malformed OHLC rows, and returns strict JSON. Use direct `yfinance` calls mainly for data outside OHLCV coverage such as company info, financial statements, options, holders, and insider transactions.

## Deep Yahoo Interfaces (references/)

Beyond the `yfinance` package, the project ships a built-in **Yahoo public-API
client** (`backtest.loaders.yahoo_client`) and two read-only agent tools that
sit on top of it. These reach Yahoo's own unauthenticated JSON endpoints
directly via `requests` (no `yfinance` install needed), share one throttled
HTTP gate (Yahoo rate-limits by source IP), and handle the cookie+crumb
handshake automatically. Each interface has its own reference doc — read the
one you need rather than loading them all:

| Doc | Covers |
|-----|--------|
| [yahoo_client.get_chart](yfinance/references/yahoo_client_get_chart.md) | Direct v8 OHLCV bars (range or epoch window) |
| [yahoo_client.get_quote_summary](yfinance/references/yahoo_client_get_quote_summary.md) | v10 quoteSummary modules (key stats, financials, ownership) |
| [yahoo_client.get_options](yfinance/references/yahoo_client_get_options.md) | v7 option chain (expirations + calls/puts) |
| [yahoo_client.search](yfinance/references/yahoo_client_search.md) | v1 instrument search by ticker/name |
| [get_options_chain tool](yfinance/references/tool_get_options_chain.md) | Agent tool: US options ladder envelope |
| [get_stock_profile tool](yfinance/references/tool_get_stock_profile.md) | Agent tool: company profile/estimates/ownership envelope |

> Path convention: `read_file` resolves paths with `skills/` as the root, so
> every link above is written with the **skill-name prefix** (`yfinance/references/...`).
> Omitting the prefix makes the read fail. Reuse this `yfinance/references/...`
> form for any new reference docs.

The Yahoo client uses the project ticker convention (`AAPL.US` → `AAPL`,
`00700.HK` → `0700.HK`); see the [Ticker Format Conversion](#ticker-format-conversion)
table below — the same rules apply across all of the interfaces above.

## Quick Start

Preferred OHLCV tool call:

```json
{
  "codes": ["AAPL.US", "700.HK"],
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "source": "yfinance",
  "interval": "1D"
}
```

If you must write a Python script for OHLCV, use the DataLoader instead of raw `yf.download`:

```python
from backtest.loaders.registry import get_loader_cls_with_fallback

loader = get_loader_cls_with_fallback("yfinance")()
data = loader.fetch(["AAPL.US", "700.HK"], "2025-01-01", "2026-01-01", interval="1D")

for symbol, df in data.items():
    print(symbol, df.tail())
```

## Ticker Format Conversion

The project uses a unified ticker format. The DataLoader automatically converts to yfinance format:

| Project Format | yfinance Format | Market |
|---------------|----------------|--------|
| `AAPL.US` | `AAPL` | US stock |
| `MSFT.US` | `MSFT` | US stock |
| `700.HK` | `0700.HK` | HK stock |
| `9988.HK` | `9988.HK` | HK stock |
| `SPY.US` | `SPY` | US ETF |

**Rules:**
- US stocks: strip the `.US` suffix → use the raw ticker
- HK stocks: keep `.HK`, pad the number to 4 digits (`700` → `0700`)

## Supported Data Types

### 1. Historical OHLCV

Prefer `get_market_data` for OHLCV whenever the tool is available:

```json
{
  "codes": ["AAPL.US", "MSFT.US", "GOOGL.US"],
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "source": "yfinance",
  "interval": "1D",
  "max_rows": 250
}
```

For script-based OHLCV analysis, use the loader:

```python
from backtest.loaders.registry import get_loader_cls_with_fallback

loader = get_loader_cls_with_fallback("yfinance")()

# Single stock
single = loader.fetch(["AAPL.US"], "2025-01-01", "2026-01-01", interval="1D")

# Specific interval
hourly = loader.fetch(["AAPL.US"], "2026-03-01", "2026-03-30", interval="1H")
```

**Supported intervals:**
- Minute-level: `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`
- Hourly: `1h`
- Daily and above: `1d`, `5d`, `1wk`, `1mo`, `3mo`

**Minute data limits:**
- `1m`: up to 7 days of history
- `2m/5m/15m/30m/60m/90m`: up to 60 days
- `1h`: up to 730 days
- `1d` and above: unlimited

### 2. Company Info

```python
ticker = yf.Ticker("AAPL")

info = ticker.info
print(f"Company: {info.get('longName')}")
print(f"Industry: {info.get('industry')}")
print(f"Market cap: {info.get('marketCap')}")
print(f"PE: {info.get('trailingPE')}")
print(f"EPS: {info.get('trailingEps')}")
print(f"Dividend yield: {info.get('dividendYield')}")
```

### 3. Financial Statements

```python
ticker = yf.Ticker("AAPL")

# Income statement (annual)
income = ticker.financials
# Income statement (quarterly)
income_q = ticker.quarterly_financials

# Balance sheet
balance = ticker.balance_sheet

# Cash flow statement
cashflow = ticker.cashflow

# Earnings data
earnings = ticker.earnings
```

### 4. Dividends and Splits

```python
ticker = yf.Ticker("AAPL")

# Dividend history
dividends = ticker.dividends

# Stock split history
splits = ticker.splits

# All corporate actions
actions = ticker.actions
```

### 5. Institutional Holdings

```python
ticker = yf.Ticker("AAPL")

# Institutional holders
holders = ticker.institutional_holders

# Major holders summary
major = ticker.major_holders

# Insider transactions
insider = ticker.insider_transactions
```

### 6. Indices and ETFs

```python
# Major indices
sp500 = yf.download("^GSPC", start="2025-01-01", end="2026-01-01", progress=False)  # S&P 500
nasdaq = yf.download("^IXIC", start="2025-01-01", end="2026-01-01", progress=False)  # NASDAQ
hsi = yf.download("^HSI", start="2025-01-01", end="2026-01-01", progress=False)      # Hang Seng Index

# ETFs
spy = yf.download("SPY", start="2025-01-01", end="2026-01-01", progress=False)
qqq = yf.download("QQQ", start="2025-01-01", end="2026-01-01", progress=False)
```

### 7. FX Rates

```python
# Currency pairs
usdcny = yf.download("CNY=X", start="2025-01-01", end="2026-01-01", progress=False)
usdhkd = yf.download("HKD=X", start="2025-01-01", end="2026-01-01", progress=False)
eurusd = yf.download("EURUSD=X", start="2025-01-01", end="2026-01-01", progress=False)
```

## Backtest Usage

### config.json Example

```json
{
  "source": "yfinance",
  "codes": ["AAPL.US", "MSFT.US"],
  "start_date": "2020-01-01",
  "end_date": "2026-03-30",
  "initial_cash": 1000000,
  "commission": 0.001,
  "extra_fields": null
}
```

### Cross-Market Auto Mode

```json
{
  "source": "auto",
  "codes": ["000001.SZ", "AAPL.US", "700.HK", "BTC-USDT"],
  "start_date": "2024-01-01",
  "end_date": "2026-03-30",
  "initial_cash": 1000000,
  "commission": 0.001,
  "extra_fields": null
}
```

`source: "auto"` routes automatically by ticker format: A-shares → tushare, HK/US stocks → yfinance, crypto → OKX.

## Notes

- **Free, no API key**: yfinance scrapes Yahoo Finance public data — no registration needed
- **Rate limits**: high-frequency requests may trigger temporary Yahoo bans — prefer batch downloads over per-ticker loops
- **Minute data range**: limited by Yahoo Finance (see table above)
- **HK tickers**: Yahoo Finance uses 4-digit numbers + `.HK`; pad with leading zeros where needed
- **Adjustment**: `auto_adjust=True` (default) returns forward-adjusted prices; the project loader uses `auto_adjust=False`
- **Timezone**: returned data includes timezone info; the DataLoader strips it automatically
- **extra_fields not supported**: yfinance via the backtest loader returns OHLCV only; PE/PB and other fundamentals require separate `yf.Ticker().info` calls
- **Comparison with Tushare**: Tushare covers deep A-share data (financials, fund flows, block trades, etc.); yfinance covers global markets but with less depth
