---
name: data-routing
category: data-source
description: The single ROUTER for every data need. Load this skill BEFORE any backtest, data-fetch, or research task to pick the best available source/tool, honour auth (env) requirements, and avoid ban-risk providers.
---
# Data Routing (Router)

This is the one router. It maps (a) every registered backtest data **source** to its
markets / auth / skill, and (b) every research **data need** to the concrete **tool**
that serves it, its market, and the env key it requires. Source names below are a
strict subset of `backtest.loaders.registry.VALID_SOURCES` (enforced by
`tests/test_data_routing_sources_subset.py`).

## Source Overview

Every name here is a registered OHLCV/backtest source in `VALID_SOURCES`.
"Runner-internal" sources are selected by the backtest runner, not authored as a
per-source skill.

| Source | Markets | Auth (env key) | Network | Skill |
|--------|---------|----------------|---------|-------|
| tushare | A-shares, funds, futures, macro | Yes (`TUSHARE_TOKEN`) | China network | tushare |
| akshare | A-shares, US, HK, futures, macro, forex | No | Unrestricted | akshare |
| yfinance | US stocks, HK stocks, ETFs | No | Needs Yahoo access | yfinance |
| okx | Crypto (OKX exchange) | No | Needs okx.com access | okx-market |
| ccxt | Crypto (100+ exchanges) | No | Needs exchange access | ccxt |
| baostock | A-shares (free daily/min) | No | China network | data-routing |
| tencent | A-shares, HK, US (never-banned) | No | Unrestricted | data-routing |
| mootdx | A-shares (TDX servers, never-banned) | No | China network | data-routing |
| futu | A/HK/US via OpenD gateway | Yes (OpenD running) | Local gateway | data-routing (runner-internal) |
| local | User CSV/parquet on disk | No | Offline | data-routing (runner-internal) |
| eastmoney | A-shares, HK, US equities | No (IP-throttled) | Unrestricted | data-routing |
| sina | US equities (daily OHLCV) | No (IP-throttled) | Unrestricted | data-routing |
| stooq | US equities (daily OHLCV) | No | Unrestricted | data-routing |
| yahoo | US, HK equities | No (IP-throttled) | Needs Yahoo access | data-routing |
| finnhub | US equities | Yes (`FINNHUB_API_KEY`) | Unrestricted | data-routing |
| alphavantage | US equities | Yes (`ALPHAVANTAGE_API_KEY`) | Unrestricted | data-routing |
| tiingo | US equities | Yes (`TIINGO_API_KEY`) | Unrestricted | data-routing |
| fmp | US equities | Yes (`FMP_API_KEY`) | Unrestricted | data-routing |

## Capability → Tool Routing

Pick the tool by the data need. "Market" is the universe the tool covers; "Env key"
is required only where listed (no key listed = free / no auth).

| Data need | Tool | Market | Env key |
|-----------|------|--------|---------|
| OHLCV price bars | `get_market_data` | A-share / US / HK / crypto / futures / forex | per-source (see Source Overview) |
| Fund flow (资金流向) | `get_fund_flow` | A-share, HK, US | — |
| Dragon-tiger (龙虎榜) | `get_dragon_tiger` | A-share | — |
| Northbound flow (北向资金) | `get_northbound_flow` | A-share | — |
| Margin trading (融资融券) | `get_margin_trading` | A-share | — |
| Block trades (大宗交易) | `get_block_trades` | A-share | — |
| Shareholder count (股东户数) | `get_shareholder_count` | A-share | — |
| Lockup expiry (限售解禁) | `get_lockup_expiry` | A-share | — |
| Sector / board taxonomy (板块) | `get_sector_info` | A-share | — |
| Sell-side research reports | `get_research_reports` | A-share | — |
| Stock news | `get_stock_news` | A-share, US, HK | — |
| SEC filings (EDGAR) | `get_sec_filings` | US | — |
| Financial statements | `get_financial_statements` | A-share, US, HK | — |
| Options chain | `get_options_chain` | US | — |
| Stock profile / fundamentals | `get_stock_profile` | US | — |
| Market screen | `screen_market` | A-share | — |
| Symbol search | `search_symbol` | A-share, US | — |
| Macro / FRED series | `get_macro_series` | Macro (US/global) | `FRED_API_KEY` |
| iWenCai NL search (问财) | `iwencai_search` | A-share | `VIBE_TRADING_IWENCAI_KEY` |

Notes:
- `get_financial_statements` reads A-share, US, and HK statements via the
  Eastmoney datacenter report API (per-market F10 report names) — an IP-throttled
  client, not the OHLCV loader of the same name.
- `get_stock_news` routes A-share (SH/SZ/BJ) to an Eastmoney news client and
  US (.US) / HK (.HK) to a Yahoo search client; a failure on one upstream is
  returned as an error envelope, never raised, so a single bad symbol never
  aborts a batch.

## Decision Tree

### Backtest scenario (writing config.json)

Use `source: "auto"` — the runner routes by symbol pattern and falls back across
same-market sources automatically. Only set a concrete source when the user asks.

### Analysis / research scenario

1. Identify the data need, then read the Capability table for the tool + env key.
2. If the need is plain OHLCV, call `get_market_data` and let source fallback run.
3. Set any required env key before calling a key-gated tool; if it is missing,
   report the missing key rather than failing silently.

### Source priority (for OHLCV by market)

- **A-shares**: tencent / mootdx (never banned) > tushare (`TUSHARE_TOKEN`) >
  baostock / akshare > eastmoney (throttled).
- **US stocks**: stooq / yahoo > tiingo / finnhub / fmp / alphavantage (key-gated) >
  sina / eastmoney (throttled) > yfinance.
- **HK stocks**: tencent > eastmoney / yahoo > yfinance.
- **Crypto**: okx (single exchange) > ccxt (multi-exchange).
- **Futures / macro / forex**: tushare > akshare.

## Symbol Format Reference

| Market | Format | Examples |
|--------|--------|----------|
| A-shares | `NNNNNN.SZ/SH/BJ` | 000001.SZ, 600000.SH, 430139.BJ |
| US stocks | `TICKER.US` | AAPL.US, MSFT.US |
| HK stocks | `NNNNN.HK` | 00700.HK, 09988.HK |
| Crypto | `SYMBOL-USDT` | BTC-USDT, ETH-USDT |
| Futures | `XXNNNN.EXCHANGE` | CU2406.SHFE |
| Forex | `XXX/YYY` | USD/CNY, EUR/USD |

## Ban-Risk & Fallback Notes

- **Prefer never-banned sources**: `tencent` and `mootdx` have no observed IP ban;
  reach for them first for A-share OHLCV when no token is set.
- **Eastmoney rate-limits by IP and must be throttled.** Every Eastmoney-backed
  tool/loader routes through the shared per-host throttle; do not hammer it. On a
  throttle/timeout, fall back to the same-market source above (tencent/baostock).
- **Sina / Yahoo also throttle by IP** — same per-host wrapper, same fallback rule.
- **Key-gated sources need their env key** (`FINNHUB_API_KEY`,
  `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `FMP_API_KEY`, `FRED_API_KEY`,
  `VIBE_TRADING_IWENCAI_KEY`, `TUSHARE_TOKEN`). If the key is absent the tool/loader
  is unavailable — route to a free same-market source instead of erroring out.
- A single failing symbol or transient HTTP error is reported inside the envelope;
  it never aborts the surrounding batch.
