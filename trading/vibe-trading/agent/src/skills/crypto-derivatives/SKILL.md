---
name: crypto-derivatives
description: Crypto-derivatives strategies — perpetual funding-rate arbitrage, futures term-structure contango/backwardation trading, and option volatility-smile / Greeks analysis.
category: crypto
---

# Crypto-Derivatives Strategies

## Overview

Covers three major crypto-derivatives strategy directions: perpetual funding-rate arbitrage, futures term-structure trading, and options strategies (volatility trading). The main exchanges are OKX and Deribit.

## Perpetual Funding-Rate Arbitrage

### Funding-Rate Mechanism

```
Perpetual contracts have no expiry and rely on the funding rate to anchor prices to spot:

Funding rate > 0: longs pay shorts (strong bullish sentiment)
Funding rate < 0: shorts pay longs (strong bearish sentiment)

Settlement frequency: OKX settles every 8 hours (00:00 / 08:00 / 16:00 UTC)
Annualized return = funding rate × 3 × 365
```

### Arbitrage Strategies

```
Positive carry arbitrage (funding rate > 0):
  Long spot + short perpetual = net delta close to zero
  Return source: collect funding every 8 hours

Reverse carry arbitrage (funding rate < 0, less common):
  Short spot (borrow coin and sell) + long perpetual
  Return source: collect funding every 8 hours
```

### Funding-Rate Signals

| Funding Rate (8h) | Annualized | Market Sentiment | Strategy Signal |
|-------------|------|---------|---------|
| > 0.1% | > 109% | Extreme greed | Short signal (rate is unsustainable) |
| 0.03-0.1% | 33-109% | Bullish bias | Positive carry arbitrage is attractive |
| 0.01-0.03% | 11-33% | Normal bullish | Positive carry arbitrage is tradable |
| -0.01~0.01% | -11~11% | Neutral | No arbitrage opportunity |
| < -0.01% | < -11% | Bearish bias | Reverse carry arbitrage or stop-loss |
| < -0.1% | < -109% | Extreme panic | Long signal (rate is unsustainable) |

### Arbitrage Risk Control

```
Risk points:
1. Insufficient margin: the derivatives leg requires margin, and extreme moves can liquidate the account
2. Funding reversal: a positive rate can suddenly turn negative, making the arbitrage unprofitable
3. Basis volatility: changes in the spot-futures basis can cause floating losses
4. Exchange risk: withdrawal limits, downtime, liquidation-mechanism differences

Risk parameters:
- Leverage: no more than 3x (arbitrage does not need high leverage)
- Margin ratio: keep >50% (far from liquidation)
- Single-coin allocation: <30% (diversification)
- Stop-loss: close when floating loss exceeds expected return over 3 months
```

## Term-Structure Trading

### Basic Concepts

```
Term structure = futures price curve across different expiries

Contango: far month > near month > spot
  - Meaning: market expects higher future prices
  - Common in bull markets or normal market conditions

Backwardation: far month < near month < spot
  - Meaning: market expects lower future prices or spot shortage
  - Common in bear markets or after extreme events
```

### Term-Structure Metrics

```python
def term_structure_spread(spot_price, futures_prices: dict) -> dict:
    """
    Args:
        spot_price: Spot price
        futures_prices: {expiry: price}, for example {'2026-06': 105000, '2026-09': 107000}
    Returns:
        Basis, annualized basis, and structure type
    """
    results = {}
    for expiry, price in futures_prices.items():
        days_to_expiry = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
        basis = (price - spot_price) / spot_price
        annualized = basis / days_to_expiry * 365
        results[expiry] = {
            'basis': basis,
            'annualized_basis': annualized,
            'days': days_to_expiry,
        }
    return results
```

### Trading Strategies

| Strategy | Action | Applicable Environment | Risk |
|------|------|---------|------|
| Cash-and-Carry | Long spot + short futures | Significant contango (annualized >15%) | Exchange risk |
| Calendar Spread | Long near month + short far month | Expect contango convergence | Basis widening |
| Reverse Calendar | Short near month + long far month | Expect backwardation convergence | Basis reversal |

### Historical Regularities of BTC Term Structure

```
- Bull market: contango annualized 15-40%, quarterly futures premium 5-10%
- Bear market: backwardation or contango annualized <5%
- Around halving: contango usually widens
- Extreme crashes: brief backwardation (such as March 12 and May 19)
```

## Options Strategies

### Overview of the Crypto Options Market

| Exchange | Underlyings | Characteristics |
|--------|------|------|
| Deribit | BTC / ETH | Largest options exchange, >80% market share |
| OKX | BTC / ETH | Second largest, liquidity still growing |
| Binance | BTC / ETH | Weaker liquidity |

### Basic Greeks

| Greek | Meaning | Crypto-Specific Characteristic |
|-------|------|-----------|
| Delta | Change in option price for a 1% move in the underlying | BTC is highly volatile, so Delta changes quickly |
| Gamma | Rate of change of Delta | ATM options have the highest Gamma |
| Theta | Time decay (per day) | Crypto trades 7x24, so there are no weekends off |
| Vega | Impact of a 1% move in implied volatility | BTC IV is often 50-120%, far above traditional assets |
| Rho | Rate sensitivity | In crypto markets, the rate proxy is DeFi yield |

### Volatility Smile / Skew

```
Characteristics of the BTC option volatility surface:
1. Smile: IV of OTM puts and OTM calls is both higher than ATM IV
2. Skew: usually OTM put IV > OTM call IV (downside-protection demand)
3. Reverse skew: in bull markets, OTM call IV may exceed OTM put IV

25Δ Risk Reversal = IV(25Δ Call) - IV(25Δ Put)
  > 0: bullish skew
  < 0: bearish skew (normal state)
  The larger the absolute value, the steeper the skew
```

### Common Options Strategies

#### 1. Short Straddle

```
Action: sell ATM call + ATM put simultaneously
Return source: time decay (Theta income)
Risk: large move in the underlying
Applicable when: IV is considered too high and the market is expected to stay range-bound

BTC parameter suggestions:
- Consider selling when IV > 80%
- Expiry: 7-14 days (faster decay)
- Margin: at least 30% of underlying notional
```

#### 2. Protective Put

```
Action: hold spot + buy OTM put
Purpose: hedge downside risk
Cost: put premium (about 2-5% of underlying value per month)
Applicable when: protecting profits in a bull market

BTC parameter suggestions:
- Strike: 10-15% below spot
- Expiry: 1-3 months
- Delta: -0.2 to -0.3
```

#### 3. Iron Butterfly

```
Action: sell ATM call + sell ATM put + buy OTM call + buy OTM put
Return source: profit when the underlying moves within a narrow range
Risk: limited (protected by OTM options)
Applicable when: low-volatility expectation

Maximum profit = premium sold - premium bought
Maximum loss = wing width - maximum profit
```

#### 4. Volatility Arbitrage

```
Action: long / short IV versus realized volatility

Long volatility:
- Buy straddle + Delta hedge
- Applicable when: IV < historical volatility (IV is low)

Short volatility:
- Sell straddle + Delta hedge
- Applicable when: IV > historical volatility (IV is high)

BTC IV reference:
- IV < 40%: extremely low (long volatility)
- IV 40-60%: normal-to-low
- IV 60-80%: normal
- IV 80-120%: elevated (short volatility)
- IV > 120%: extremely high (short volatility, but risk is large)
```

## Analysis Framework

### Daily Monitoring Metrics

```
1. Perpetual funding rate (8h / annualized)
2. BTC quarterly-futures basis
3. 25Δ Risk Reversal
4. ATM implied volatility
5. Option put/call ratio
6. Option open interest
```

### Strategy Selection Decision Tree

```
Market environment judgment:
├── High funding rate (>0.05%) + high IV (>80%)
│   └── Positive carry arbitrage + short volatility
├── Low funding rate + low IV (<50%)
│   └── Stay out of carry arbitrage + long volatility
├── Significant contango (annualized >20%)
│   └── Cash-and-Carry
└── Backwardation
    └── Reduce exposure / hedge / buy protective puts
```

## Output Format

```markdown
## Crypto-Derivatives Analysis

### Market Snapshot
| Metric | BTC | ETH |
|------|-----|-----|
| Spot price | $95,000 | $3,200 |
| Perpetual funding (8h) | 0.035% | 0.028% |
| Annualized funding | 38.3% | 30.7% |
| Quarterly basis (annualized) | 18.5% | 15.2% |
| ATM IV (30d) | 65% | 72% |
| 25Δ RR | -3.2% | -4.5% |

### Strategy Suggestions
| Strategy | Direction | Expected Annualized Return | Risk Level |
|------|------|---------|---------|
| BTC funding-rate arbitrage | Short perpetual + long spot | 25-35% | Medium |
| ETH Calendar Spread | Long near month / short far month | 12-18% | Medium-low |
| BTC Short Strangle | Sell OTM call + put | Collect premium | High |

### Risk Warnings
- ...
```

## Notes

1. **This system is for backtest research only**: it does not execute live trades; derivatives analysis is for research and backtesting
2. **Crypto trades 7x24**: Theta decay never stops, unlike traditional options
3. **Liquidity concentration**: BTC / ETH options are concentrated on Deribit; liquidity in other coins is extremely poor
4. **Extreme volatility**: 10-20% single-day BTC moves are not rare, so margin management is critical
5. **Exchange risk**: centralized exchanges can freeze assets or fail; diversify across venues
6. **Data acquisition**: OKX data is available through the OKX data source, while Deribit requires an additional interface
7. **Regulatory risk**: regulation of crypto derivatives is tightening across jurisdictions, so strategy compliance must be assessed separately
