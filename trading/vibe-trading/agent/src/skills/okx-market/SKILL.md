---
name: okx-market
description: OKX cryptocurrency market data interface. Uses the OKX V5 REST API to retrieve spot, derivatives, index, and other crypto market data, including real-time prices, candlesticks, funding rates, open interest, and more. No authentication required, free to use.
category: data-source
---
# OKX Market

## Overview

The OKX V5 REST API provides comprehensive cryptocurrency market data covering spot, perpetual swaps, delivery futures, options, and more. All market-data endpoints are public and can be called directly without authentication. The data comes from OKX, the world's second-largest cryptocurrency exchange.

## Quick Start

- Install a Python runtime (Python 3.9+ recommended) and the required `requests` dependency.

```bash
pip install requests pandas
```

- No account registration or token configuration is required. Market-data endpoints are fully open.
- Review the endpoint documentation below and locate the interface you need.
- Use Python code to retrieve data according to the documentation. Example for the **spot ticker** endpoint:

```python
import requests
import pandas as pd

BASE_URL = "https://www.okx.com/api/v5"

# Get the latest BTC-USDT market quote
resp = requests.get(f"{BASE_URL}/market/ticker", params={"instId": "BTC-USDT"})
data = resp.json()["data"][0]
print(f"BTC last price: {data['last']}  24h change: {float(data['last'])/float(data['open24h'])*100-100:.2f}%")
```

## Parameter Format Reference

- **Instrument format (`instId`)**:
  - Spot: `BTC-USDT`, `ETH-USDT`
  - Perpetual swap: `BTC-USDT-SWAP`, `ETH-USDT-SWAP`
  - Delivery futures: `BTC-USDT-250328` (expiry date in `YYMMDD`)
  - Options: `BTC-USD-250328-95000-C` (expiry-strike-C/P)
  - Index: `BTC-USD`, `ETH-USD`
- **Candlestick interval (`bar`)**: `1m`, `3m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `6H`, `12H`, `1D`, `1W`, `1M`
- **Instrument type (`instType`)**: `SPOT` (spot), `SWAP` (perpetual), `FUTURES` (delivery), `OPTION` (option)
- **Timestamp**: millisecond Unix timestamp (for example `1773763200000`)
- **Response format**: JSON. `code=0` indicates success, and data is returned in the `data` field

> Link convention: every link to `references/` in this document is written with the **skill-name prefix** (for example `okx-market/references/...`). The `read_file` tool resolves paths rooted at `skills/`, so omitting the prefix makes the read fail. When adding new skill docs, always use the `<skill-name>/references/...` form.

## Python Script Examples

- [Market data retrieval example](okx-market/scripts/market_data_example.py)
- [Candlestick data retrieval example](okx-market/scripts/candle_data_example.py)

## Market Data Endpoint List

| ID | Endpoint Path | Title (Detailed Documentation) | Category | Description |
| ---: | :--- | :--- | :--- | :--- |
| 1 | /market/ticker | [Single Ticker](okx-market/references/现货行情/单个行情.md) | Spot Market | Retrieve the latest market data for a single trading instrument, including last price, bid/ask, 24h volume, and more |
| 2 | /market/tickers | [Batch Tickers](okx-market/references/现货行情/批量行情.md) | Spot Market | Retrieve all market data for a given instrument class (`SPOT`/`SWAP`/`FUTURES`/`OPTION`) in batch |
| 3 | /market/candles | [Candlestick Data](okx-market/references/现货行情/K线数据.md) | Spot Market | Retrieve candlestick (OHLCV) data with multiple supported intervals |
| 4 | /market/trades | [Recent Trades](okx-market/references/现货行情/最近成交.md) | Spot Market | Retrieve recent trade-level details |
| 5 | /public/instruments | [Instrument List](okx-market/references/现货行情/交易产品列表.md) | Spot Market | Retrieve metadata for all tradable instruments, including minimum order size and price precision |
| 6 | /market/books | [Order Book Depth](okx-market/references/现货行情/深度数据.md) | Spot Market | Retrieve bid/ask order book depth data |
| 7 | /public/funding-rate | [Funding Rate](okx-market/references/合约行情/资金费率.md) | Derivatives Market | Retrieve current and historical funding rates for perpetual contracts |
| 8 | /public/funding-rate-history | [Historical Funding Rate](okx-market/references/合约行情/历史资金费率.md) | Derivatives Market | Retrieve historical funding-rate data for perpetual contracts |
| 9 | /public/mark-price | [Mark Price](okx-market/references/合约行情/标记价格.md) | Derivatives Market | Retrieve mark prices for derivatives, used for PnL and liquidation calculations |
| 10 | /public/open-interest | [Open Interest](okx-market/references/合约行情/持仓量.md) | Derivatives Market | Retrieve open-interest data for derivatives |
| 11 | /public/price-limit | [Price Limit](okx-market/references/合约行情/限价.md) | Derivatives Market | Retrieve the current maximum and minimum price limits for derivatives |
| 12 | /market/index-tickers | [Index Tickers](okx-market/references/指数行情/指数行情.md) | Index Market | Retrieve index price market data |
| 13 | /market/index-candles | [Index Candles](okx-market/references/指数行情/指数K线.md) | Index Market | Retrieve index candlestick data |
