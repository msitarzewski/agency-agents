---
name: akshare
category: data-source
description: AKShare financial data aggregator (18k+ stars). Free, no API key. Covers A-shares, US, HK, futures, macro, forex. Primary fallback for tushare and yfinance.
---

## Overview

AKShare is a completely free, open-source Python financial data library. No registration or API key required. It aggregates data from public sources (Sina, East Money, etc.) covering Chinese and global markets.

- GitHub: https://github.com/akfamily/akshare (18k+ stars)
- Install: `pip install akshare`

## Quick Start

```python
import akshare as ak

# A-share daily OHLCV (前复权)
df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                         start_date="20240101", end_date="20260101", adjust="qfq")

# US stock daily
df = ak.stock_us_hist(symbol="105.AAPL", period="daily",
                       start_date="20240101", end_date="20260101", adjust="qfq")

# HK stock daily
df = ak.stock_hk_hist(symbol="00700", period="daily",
                       start_date="20240101", end_date="20260101", adjust="qfq")
```

## Top 10 High-Frequency Interfaces

### A-shares

| Function | Description | Key Params |
|----------|-------------|------------|
| `stock_zh_a_hist()` | A-share OHLCV | symbol, period, start_date, end_date, adjust |
| `stock_zh_a_spot_em()` | Real-time A-share quotes | (none) |
| `stock_individual_info_em()` | Stock basic info | symbol |
| `stock_zh_a_hist_min_em()` | Intraday bars | symbol, period(1/5/15/30/60) |

### US / HK

| Function | Description | Key Params |
|----------|-------------|------------|
| `stock_us_hist()` | US stock OHLCV | symbol (e.g. "105.AAPL"), period, start_date, end_date |
| `stock_hk_hist()` | HK stock OHLCV | symbol (e.g. "00700"), period, start_date, end_date |

### Macro / Forex / Futures

| Function | Description |
|----------|-------------|
| `macro_china_gdp()` | China GDP data |
| `macro_china_cpi()` | China CPI data |
| `futures_main_sina()` | Futures main contract quotes |
| `currency_boc_sina()` | BOC forex rates |

## Column Names

AKShare returns Chinese column names by default:

| Chinese | English | Description |
|---------|---------|-------------|
| 日期 | date | Trade date |
| 开盘 | open | Open price |
| 最高 | high | High price |
| 最低 | low | Low price |
| 收盘 | close | Close price |
| 成交量 | volume | Volume |
| 成交额 | amount | Turnover |
| 涨跌幅 | pct_change | % change |
| 换手率 | turnover_rate | Turnover rate |

## Date Format

- Input: `YYYYMMDD` string (e.g. `"20240101"`)
- Output: `日期` column as string, convert with `pd.to_datetime()`

## Symbol Format

- A-shares: pure digits `"000001"` (no .SZ suffix)
- US stocks: `"105.AAPL"` (NASDAQ prefix 105), `"106.BABA"` (NYSE prefix 106)
- HK stocks: `"00700"` (5-digit zero-padded)

## Built-in Loader

The project has a built-in AKShare DataLoader at `backtest/loaders/akshare_loader.py`. When backtesting, the runner automatically falls back to AKShare when tushare/yfinance are unavailable.

## Reference Docs

For less common interfaces, see the `references/` subdirectory or the official docs at https://akshare.akfamily.xyz/
