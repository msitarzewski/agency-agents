---
name: mootdx
category: data-source
description: Mootdx A-share market data via TCP-direct 通达信 servers. Free, no API key, no IP rate limits. Use as the stable A-share OHLCV fallback when akshare's East Money scrape is throttled.
---

## Overview

Mootdx talks the native 通达信 (TDX) binary protocol over TCP, bypassing the HTTP scrapers that periodically fail under load (akshare → East Money is the canonical example). Public market data only — no token, no per-IP throttling, no captcha.

- GitHub: https://github.com/mootdx/mootdx
- Install: `pip install mootdx && pip install 'httpx>=0.28.1'`

> Mootdx pins `httpx<0.26` in `setup.py`, but only uses basic `httpx.Client/get` APIs that are forward-compatible. The second `pip install` restores the modern httpx that the rest of Vibe-Trading (MCP server, fastmcp) needs.

## Quick Start

```python
from mootdx.quotes import Quotes

client = Quotes.factory(market="std")  # std = 沪/深/京; ext = 期货/期权 (upstream-broken)

# Daily OHLCV with a date range (preferred API).
df = client.get_k_data(code="000001", start_date="2025-01-01", end_date="2025-02-01")

# Intraday — offset-from-latest only, no native date range.
df_15m = client.bars(symbol="600519", frequency=1, offset=800)
```

## Frequency Codes

`bars(frequency=N)` uses integer codes from `mootdx.consts`:

| Code | Bar |
|------|-----|
| 8 | 1m |
| 0 | 5m |
| 1 | 15m |
| 2 | 30m |
| 3 | 1H |
| 4 | 1D |
| 5 | 1W |
| 6 | 1M |

`get_k_data()` is **daily only** but accepts `start_date / end_date`. For intraday, `bars()` returns the latest N rows — the built-in loader over-fetches `offset=800` then clips to the requested window.

## Key Methods

| Method | Use | Returns |
|--------|-----|---------|
| `get_k_data(code, start_date, end_date)` | Daily OHLCV with date range | `[open, close, high, low, vol, amount, date, code]` |
| `bars(symbol, frequency, offset=800)` | Intraday / weekly / monthly | `[open, close, high, low, vol, amount, datetime, volume, ...]` |
| `minute(symbol)` | Current trading day 1m bars | Same schema as `bars()` |
| `quotes(symbol)` | Real-time L1 snapshot | `{price, bid, ask, volume, ...}` |
| `stocks(market)` | List all tickers on an exchange | DataFrame of `code/name` |
| `F10(symbol)` / `finance(symbol)` | Fundamentals snapshot | Heterogeneous dict |

## Symbol Format

- Pure 6-digit: `"000001"`, `"600519"`, `"835174"` — mootdx auto-detects exchange from prefix:
  - `60x / 68x` → SH
  - `00x / 30x / 002 / 003` → SZ
  - `4x / 8x` → BJ
- The built-in loader also accepts `"000001.SZ"`, `"600519.SH"`, `"835174.BJ"` and strips the suffix.

## Column Names

`get_k_data()` returns lowercase English: `open / close / high / low / vol / amount / date / code`. The built-in loader renames `vol` → `volume` to match the project's OHLCV contract.

`bars()` returns the same OHLC columns plus a duplicate `volume` (alongside the legacy `vol`), a `datetime` string column, and decomposed `year / month / day / hour / minute` columns.

## Built-in Loader

`backtest/loaders/mootdx_loader.py` is registered as the `mootdx` source. Fallback chain for `a_share` is `[tushare, mootdx, akshare]` — tushare wins when a token is present; mootdx wins when no token but TCP egress works; akshare is the broadest fallback.

```python
from backtest.runner import run
result = run(strategy=..., source="mootdx")  # explicit override
```

## Known Limitations

| Limitation | Workaround |
|------------|------------|
| 北交所 (BJ): `get_k_data` raises `KeyError`, `bars()` returns empty (upstream missing data) | Loader logs a warning and skips BJ symbols — use akshare or tushare |
| Extended market (futures/options) returns empty as of v0.11.7 (upstream issue) | Use tushare/akshare for futures |
| Each `bars()` page is 800 rows; loader paginates back up to 25 pages (≈10y daily / ≈5y 1H / ≈3mo 1m) | For longer 1m history use tushare minute bars |
| Server selection has cold-start latency (first call picks the fastest server) | First call may be ~2s slower |
| Returns data in 前复权 by default — no API parameter for 不复权 | Use tushare/akshare if raw prices are required |

## Reference Docs

- Mootdx 文档: https://www.mootdx.com/
- 通达信协议参考: https://github.com/rainx/pytdx
