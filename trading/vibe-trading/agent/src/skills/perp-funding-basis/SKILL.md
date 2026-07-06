---
name: perp-funding-basis
description: Perpetual futures funding rate analysis and cash-carry basis trading — funding rate regimes, annualized basis signals, carry trade construction, and funding rate arbitrage between exchanges.
category: crypto
---
# Perpetual Funding Rate & Basis Trading

## Overview

Analyze perpetual futures funding rates and spot-futures basis to identify carry trade opportunities, market positioning extremes, and directional sentiment signals. Funding rates are the single most important microstructure indicator in crypto derivatives — they reveal real-time leverage positioning and crowd sentiment.

## Core Concepts

### 1. Funding Rate Mechanics

Perpetual futures have no expiry date. Instead, a **funding rate** is exchanged between longs and shorts every 8 hours (on most exchanges) to keep the perpetual price anchored to the spot price.

```
If perp price > spot price → funding rate positive → longs pay shorts
If perp price < spot price → funding rate negative → shorts pay longs
```

**OKX funding rate schedule**: payments at 00:00, 08:00, 16:00 UTC

**Annualized funding rate:**
```python
# OKX funding rate is per 8-hour period
# Annualized = rate × 3 (per day) × 365
funding_rate_8h = 0.01  # 0.01% per 8h
annualized = funding_rate_8h * 3 * 365  # = 10.95% annualized
```

### 2. Funding Rate Signal Framework

| Funding Rate (8h) | Annualized | Market State | Signal |
|--------------------|------------|-------------|--------|
| > +0.05% | > +54.75% | Extreme long crowding | Contrarian short / reduce longs |
| +0.02% to +0.05% | +21.9% to +54.75% | Elevated long bias | Cautious, carry trade viable |
| +0.005% to +0.02% | +5.5% to +21.9% | Mild long bias | Neutral to mild bullish |
| -0.005% to +0.005% | -5.5% to +5.5% | Balanced | Neutral |
| -0.02% to -0.005% | -21.9% to -5.5% | Mild short bias | Neutral to mild bearish |
| < -0.02% | < -21.9% | Short squeeze territory | Contrarian long / reduce shorts |

**Funding rate regime detection:**
```python
def funding_regime(rates_7d):
    """Classify funding rate regime from 7-day history."""
    avg = sum(rates_7d) / len(rates_7d)
    consecutive_positive = all(r > 0 for r in rates_7d[-3:])
    consecutive_negative = all(r < 0 for r in rates_7d[-3:])

    if avg > 0.03 and consecutive_positive:
        return "overheated_long"       # High risk of long squeeze
    elif avg > 0.01 and consecutive_positive:
        return "bullish_carry"          # Good carry trade environment
    elif avg < -0.02 and consecutive_negative:
        return "overheated_short"       # High risk of short squeeze
    elif avg < -0.005 and consecutive_negative:
        return "bearish_carry"          # Inverse carry trade
    else:
        return "neutral"
```

### 3. Spot-Futures Basis Analysis

**Basis = Futures price - Spot price**

For dated futures (quarterly), basis reflects cost-of-carry expectations:

```python
# Annualized basis
def annualized_basis(futures_price, spot_price, days_to_expiry):
    basis_pct = (futures_price - spot_price) / spot_price
    annualized = basis_pct * (365 / days_to_expiry)
    return annualized

# Example: BTC spot $65,000, quarterly future $66,500, 45 days to expiry
# Basis: 2.31%, Annualized: 18.7%
```

**Basis signal interpretation:**

| Annualized Basis | Market State | Signal |
|-----------------|-------------|--------|
| > 30% | Extreme contango, euphoric leverage | Sell basis (cash-carry), top warning |
| 15-30% | Elevated contango, bullish leverage | Carry trade attractive |
| 5-15% | Normal contango | Neutral, mild bullish |
| 0-5% | Flat basis | Low conviction, wait for direction |
| < 0% (backwardation) | Bearish, forced selling | Contrarian long, extreme pessimism |

### 4. Cash-Carry Arbitrage (Delta-Neutral)

**Strategy: buy spot + sell perpetual futures → collect funding rate**

```python
# Cash-carry trade P&L
def carry_trade_pnl(spot_entry, funding_rates, position_size):
    """
    Delta-neutral carry: long spot + short perp
    P&L comes purely from funding rate collection.
    """
    total_funding_collected = 0
    for rate in funding_rates:
        if rate > 0:  # Longs pay shorts → we collect as short
            total_funding_collected += rate * position_size
        else:  # Shorts pay longs → we pay as short
            total_funding_collected += rate * position_size  # This is negative

    return total_funding_collected

# Example: $100,000 position, avg funding +0.015% per 8h, 30 days
# Revenue: 0.015% × 3 × 30 × $100,000 = $1,350 (16.2% annualized)
```

**Carry trade execution on OKX:**
1. Buy spot BTC-USDT on OKX spot market
2. Open equal-sized short BTC-USDT-SWAP on OKX perpetual
3. Net delta = 0 (spot long cancels perp short)
4. Collect positive funding rate every 8 hours
5. Close both legs when funding rate turns negative or basis compresses

**Risk factors:**
- Funding rate can flip negative → carry becomes a cost
- Liquidation risk on short perp if insufficient margin (use 3-5x max leverage)
- Exchange counterparty risk (keep position across 2-3 exchanges)
- Basis can widen further before mean-reverting → mark-to-market loss on short leg

### 5. Cross-Exchange Funding Arbitrage

Different exchanges have different funding rates for the same asset. Arbitrage the spread:

```python
# Example: BTC-USDT perpetual funding rates
exchange_rates = {
    "OKX": 0.015,       # +0.015% per 8h
    "Binance": 0.020,   # +0.020% per 8h
    "Bybit": 0.025,     # +0.025% per 8h
}

# Strategy: short on highest funding (Bybit) + long on lowest funding (OKX)
# Net carry = 0.025% - 0.015% = 0.010% per 8h
# Annualized: 0.010% × 3 × 365 = 10.95%
# Risk: execution cost + potential for rates to converge/flip
```

### 6. Funding Rate as Directional Indicator

**Divergence signals (most powerful):**

| Price Action | Funding Rate | Interpretation | Signal |
|-------------|-------------|----------------|--------|
| Price making new highs | Funding declining | Longs not chasing → distribution | Bearish divergence |
| Price making new lows | Funding rising (less negative) | Shorts not pressing → accumulation | Bullish divergence |
| Price consolidating | Funding spiking positive | Leverage building without breakout | Squeeze risk |
| Price consolidating | Funding deeply negative | Shorts paying heavy cost to maintain | Short squeeze imminent |

**Historical pattern statistics (BTC):**
- Funding > +0.05% for 3+ consecutive periods → 70% probability of a 5-10% correction within 7 days
- Funding < -0.03% for 3+ consecutive periods → 65% probability of a 5-15% bounce within 7 days
- These are contrarian signals; funding rate extremes indicate crowded positioning

### 7. Open Interest × Funding Rate Matrix

```python
# Combined OI + Funding signal
def oi_funding_matrix(oi_change_24h_pct, funding_rate):
    if oi_change_24h_pct > 5 and funding_rate > 0.03:
        return "leveraged_long_buildup"    # High risk, squeeze potential
    elif oi_change_24h_pct > 5 and funding_rate < -0.01:
        return "leveraged_short_buildup"   # Short squeeze potential
    elif oi_change_24h_pct < -5 and funding_rate > 0:
        return "long_liquidation"          # Forced long closing
    elif oi_change_24h_pct < -5 and funding_rate < 0:
        return "short_liquidation"         # Forced short closing
    elif abs(oi_change_24h_pct) < 2 and abs(funding_rate) < 0.005:
        return "quiet_market"              # Low conviction, wait
    else:
        return "mixed"
```

## Data Access

### Via OKX API

```python
# Funding rate history
# GET /api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP

# Current funding rate
# GET /api/v5/public/funding-rate?instId=BTC-USDT-SWAP

# Open interest
# GET /api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP
```

Use `load_skill("okx-market")` for OKX data retrieval patterns.

### Key Metrics to Track

| Metric | Source | Frequency | Alert Threshold |
|--------|--------|-----------|-----------------|
| BTC funding rate (8h) | OKX / Binance | Every 8h | > +0.05% or < -0.03% |
| ETH funding rate (8h) | OKX / Binance | Every 8h | > +0.05% or < -0.03% |
| Annualized basis (quarterly) | OKX | Continuous | > 30% or < 0% |
| BTC open interest change | OKX | Hourly | > ±5% in 24h |
| Cross-exchange funding spread | Multi-exchange | Every 8h | Spread > 0.02% |

## Output Format

```
## Funding Rate & Basis Analysis — [Asset]

### Current Funding Rates
| Exchange | 8h Rate | Annualized | Regime |
|----------|---------|------------|--------|
| OKX | +0.015% | +16.4% | bullish_carry |
| Binance | +0.020% | +21.9% | bullish_carry |

### Basis Structure
- **Spot price**: $XX,XXX
- **Perp price**: $XX,XXX (premium: X.XX%)
- **Quarterly futures**: $XX,XXX (annualized basis: X.X%)
- **Basis regime**: [contango / flat / backwardation]

### Funding History (7-day)
- **Average**: +X.XXX%
- **Trend**: [rising / stable / declining]
- **Consecutive direction**: [X periods positive/negative]

### Open Interest
- **Current OI**: $X.XB
- **24h change**: [+/-X%]
- **OI × Funding signal**: [leveraged_long_buildup / quiet / etc.]

### Carry Trade Opportunity
- **Best carry**: [short on Exchange X, long spot]
- **Expected annualized yield**: X.X%
- **Risk**: [funding flip probability, liquidation distance]

### Directional Signal
- **Funding regime**: [overheated / bullish / neutral / bearish / oversold]
- **Divergence**: [none / bullish / bearish]
- **Confidence**: [high / medium / low]
```

## Notes

- Funding rates are exchange-specific; always compare across OKX, Binance, and Bybit for the full picture
- Extremely high funding rates are a **cost** for longs, not a bullish signal — they indicate overcrowded positioning
- Cash-carry trades have execution risk: slippage on entry/exit, funding rate flipping, and exchange downtime during volatility
- Basis and funding rate signals work best when combined with on-chain data (MVRV, exchange flows)
- This framework is for research purposes only and does not constitute investment advice
