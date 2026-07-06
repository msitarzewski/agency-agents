---
name: cross-market-strategy
description: Write signal_engine.py for portfolios spanning multiple markets (A-shares + crypto, equity + forex, etc.)
category: strategy
---

## When to Use

When the user requests a backtest with codes from **different markets** — e.g. `["000001.SZ", "BTC-USDT"]` or `["AAPL.US", "EUR/USD", "600519.SH"]`.

The `CompositeEngine` handles calendar alignment, shared capital, and market rules automatically. The strategy only needs to output per-symbol signals.

## Key Concepts

### 1. Market Classification in generate()

Group symbols by market type and apply market-specific indicator parameters:

```python
def generate(self, data_map):
    groups = {}
    for code, df in data_map.items():
        market = self._detect_market(code)
        groups.setdefault(market, {})[code] = df

    signals = {}
    for market, market_data in groups.items():
        params = MARKET_PARAMS[market]
        for code, df in market_data.items():
            signals[code] = self._market_signal(df, params)
    return signals
```

### 2. Per-Market Parameter Tables

Different markets have very different dynamics. Using the same parameters everywhere produces poor results.

| Parameter | A-Share | Crypto | US Equity | Forex |
|-----------|---------|--------|-----------|-------|
| MA fast | 5 | 7 | 10 | 10 |
| MA slow | 20 | 25 | 50 | 30 |
| RSI period | 14 | 10 | 14 | 14 |
| Vol lookback | 20 | 14 | 20 | 20 |
| Typical daily vol | 1-2% | 3-8% | 1-2% | 0.3-0.8% |

### 3. Volatility-Adjusted Weights (Critical)

BTC daily vol ~ 5%, A-share daily vol ~ 1.5%. Without vol-adjustment, crypto eats the entire risk budget.

```python
def _vol_adjust(self, signals, data_map):
    vols = {}
    for code, df in data_map.items():
        ret = df["close"].pct_change().dropna()
        vols[code] = ret.rolling(20).std().iloc[-1] if len(ret) > 20 else ret.std()

    inv_vols = {c: 1.0 / (v + 1e-10) for c, v in vols.items()}
    total_inv = sum(inv_vols.values())

    adjusted = {}
    for code, sig in signals.items():
        weight = inv_vols[code] / total_inv * len(signals)
        adjusted[code] = (sig * weight).clip(-1.0, 1.0)
    return adjusted
```

### 4. Cross-Market Signal Patterns

1. **Momentum spillover**: BTC 7-day momentum as overlay for A-share tech sectors
2. **Risk-on/Risk-off**: USD/CNH rate + VIX proxy to reduce equity exposure
3. **Hedging**: Long A-shares + short crypto delta as tail hedge
4. **Correlation regime**: When rolling correlation > 0.6, reduce to single-market exposure; when < 0.2, maximize diversification

### 5. What the Engine Handles (Don't Worry About)

- **Trading calendar alignment**: signals are shifted on each symbol's own calendar, then ffill'd to unified dates
- **Market rules**: T+1 for A-shares, funding fees for crypto, swap for forex — all per-symbol
- **Capital allocation**: shared pool, strategy just sets target weights via signals
- **Commission/slippage**: dispatched to correct sub-engine per symbol

## config.json for Cross-Market

```json
{
  "source": "auto",
  "codes": ["000001.SZ", "BTC-USDT"],
  "start_date": "2024-01-01",
  "end_date": "2025-03-31",
  "interval": "1D",
  "initial_cash": 1000000,
  "engine": "daily"
}
```

- `source` **must** be `"auto"` for cross-market (routes each symbol to its loader)
- `extra_fields` should be `null` (not all markets support fundamentals)
- `leverage` defaults to 1.0 (CompositeEngine inherits from config)

## Market Detection Heuristics

| Pattern | Market |
|---------|--------|
| `000001.SZ`, `600519.SH` | A-share |
| `AAPL.US` | US equity |
| `700.HK` | HK equity |
| `BTC-USDT` | Crypto |
| `IF2406.CFFEX` | China futures |
| `ESZ4` | Global futures |
| `EUR/USD` | Forex |

## Supporting Files

- [example_signal_engine.py](example_signal_engine.py) — complete cross-market strategy example
