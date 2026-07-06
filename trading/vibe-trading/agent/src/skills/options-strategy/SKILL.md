---
name: options-strategy
description: Options strategy framework supporting Black-Scholes pricing, Greeks analysis, and multi-leg backtesting. Suitable for cryptocurrency and equity options.
category: asset-class
---

## Purpose

Backtesting of option portfolio strategies. Starting from the underlying price, the engine synthesizes theoretical option prices with the Black-Scholes model, then simulates PnL, Greeks exposure, and expiration exercise for multi-leg option portfolios.

Applicable scenarios:
- Hedging strategies (`covered call`, `protective put`)
- Volatility trading (`straddle`, `strangle`)
- Spread strategies (`iron condor`, `butterfly`, `calendar spread`)
- Option pricing analysis and Greeks sensitivity research

## Supported Strategy Types

| Strategy | Structure | Applicable Market View |
|------|------|----------|
| Covered Call | Hold underlying + short call | Mildly bullish, collect premium |
| Protective Put | Hold underlying + long put | Bullish but wants downside protection |
| Straddle | Buy same-strike call + put | Expect large movement, direction uncertain |
| Strangle | Buy different-strike call + put | Expect large movement, lower cost |
| Iron Condor | Sell put spread + sell call spread | Range-bound market, collect premium |
| Butterfly | Buy low call + sell 2 middle calls + buy high call | Expect narrow-range movement |
| Calendar Spread | Sell near-month + buy far-month at same strike | Exploit differences in time decay |

## `OptionsSignalEngine` Interface

Write the strategy in `code/signal_engine.py`, with class name `SignalEngine`, implementing the `generate` method:

```python
class SignalEngine:
    """Option strategy signal engine."""

    def generate(self, data_map: dict) -> list:
        """Generate option trading instructions.

        Args:
            data_map: code -> DataFrame (columns: open, high, low, close, volume)

        Returns:
            List of trading instructions. Each instruction has the format:
            {
                "date": "2024-01-15",        # Trading date
                "action": "open" / "close",  # Open or close position
                "underlying": "BTC-USDT",    # Underlying code
                "legs": [                    # List of option legs
                    {
                        "type": "call" / "put",  # Option type
                        "strike": 50000,          # Strike price
                        "expiry": "2024-02-15",   # Expiration date
                        "qty": 1                  # Quantity (positive = long, negative = short)
                    }
                ]
            }
        """
```

### Multi-Leg Combination Example

Iron Condor opening signal:

```python
{
    "date": "2024-01-15",
    "action": "open",
    "underlying": "000300.SH",
    "legs": [
        {"type": "put",  "strike": 3800, "expiry": "2024-02-15", "qty": -1},  # Sell put
        {"type": "put",  "strike": 3700, "expiry": "2024-02-15", "qty":  1},  # Buy protective put
        {"type": "call", "strike": 4200, "expiry": "2024-02-15", "qty": -1},  # Sell call
        {"type": "call", "strike": 4300, "expiry": "2024-02-15", "qty":  1},  # Buy protective call
    ]
}
```

## `config.json` Format

```json
{
    "codes": ["000300.SH"],
    "start_date": "2020-01-01",
    "end_date": "2024-12-31",
    "source": "tushare",
    "engine": "options",
    "initial_cash": 1000000,
    "commission": 0.001,
    "options_config": {
        "risk_free_rate": 0.05,
        "iv_source": "historical",
        "contract_multiplier": 1.0
    }
}
```

Key fields:
- `engine` must be set to `"options"` so the runner selects the option backtest engine
- `options_config.risk_free_rate`: risk-free rate, default `0.05`
- `options_config.iv_source`: volatility source, currently supports `"historical"` (30-day rolling historical volatility computed from underlying closes)
- `options_config.contract_multiplier`: contract multiplier, default `1.0`

## BS Model Principles

Black-Scholes formula (European options):

```
Call = S * N(d1) - K * e^(-rT) * N(d2)
Put  = K * e^(-rT) * N(-d2) - S * N(-d1)

d1 = [ln(S/K) + (r + sigma^2/2) * T] / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)
```

Where `S` = underlying price, `K` = strike, `T` = time to expiry in years, `r` = risk-free rate, `sigma` = volatility, and `N()` = cumulative distribution function of the standard normal.

This engine starts from the underlying daily price series, substitutes historical volatility for implied volatility, and computes theoretical option prices through the BS formula. This is a synthetic-data mode, meaning no real option market data is required.

## Greeks Meaning and Usage

| Greek | Meaning | Usage |
|-------|------|------|
| Delta | Change in option price for a 1-unit move in the underlying | Directional exposure management, hedge-ratio calculation |
| Gamma | Change in Delta for a 1-unit move in the underlying | Measures hedge stability; high Gamma = frequent rebalancing required |
| Theta | Time decay of option value per day (usually negative) | Time-value management, source of return for short-option strategies |
| Vega | Change in option price for a 1% volatility move | Core metric for volatility trading, measures volatility exposure |

The backtest engine computes portfolio-level Greeks aggregates on each trading day and outputs them to `greeks.csv`.

## Common Pitfalls

### Volatility Smile

The BS model assumes constant volatility, but in real markets implied volatility differs across strikes and expiries (volatility smile / skew). This engine approximates with historical volatility, so pricing may be biased for deep OTM / deep ITM options. Strategy design should avoid over-reliance on pricing precision at extreme strikes.

### Time Decay (Theta Decay)

Theta decay is not linear — the closer the option is to expiry, the faster the decay. The last 30 days decay much faster than the prior 30 days. Short-vol strategies benefit from this, but Gamma risk also rises sharply near expiry.

### Early Exercise

This engine supports European options only (exercise only at expiry), not American options. In scenarios with meaningful early-exercise value (for example, deep ITM puts or calls on high-dividend underlyings), pricing will be biased.

### Liquidity and Slippage

In synthetic-data mode there are no bid-ask spreads or liquidity constraints. In real trading, deep OTM options have poor liquidity and wide spreads, so backtest results will be overly optimistic.

### Contract Multiplier

Option contract multipliers differ across markets (for example, China A-share ETF options often use a 10,000 multiplier, while crypto is typically 1). Make sure `options_config.contract_multiplier` is set correctly.

## Artifact Description

After backtesting, the following files are generated in the `artifacts/` directory:

| File | Contents |
|------|------|
| `equity.csv` | Daily equity, cash, market value of holdings |
| `metrics.csv` | Return, Sharpe ratio, maximum drawdown, and similar metrics |
| `trades.csv` | Trade-by-trade records (open / close / exercise / expire) |
| `greeks.csv` | Daily portfolio Greeks aggregates (`delta/gamma/theta/vega`) |
| `ohlcv_{code}.csv` | Raw underlying candlestick data |

## Pricing Tool

The Agent can call the `options_pricing` tool for one-off pricing:

```
Call the options_pricing tool with:
  spot: 50000
  strike: 52000
  expiry_days: 30
  volatility: 0.6
  option_type: "call"
```

It returns the theoretical price and Greeks, which is suitable for interactive analysis.
