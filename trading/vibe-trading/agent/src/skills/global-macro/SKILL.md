---
name: global-macro
description: Global macro analysis framework (central bank policy transmission / FX forecasting / geopolitical risk / capital flows), used to build macro factor signals that drive cross-asset allocation.
category: analysis
---
# Global Macro Analysis

## Overview

Builds a macro analysis framework from three dimensions: central-bank policy, exchange-rate regimes, and geopolitics. Outputs quantifiable macro factor signals to drive cross-asset allocation decisions. Core logic: macro cycles determine major asset direction, while micro-level timing is delegated to other skills.

## Core Concepts

### 1. Central Bank Policy Transmission Chain

```
Policy-rate changes → government bond yield curve → credit spreads → financing costs for the real economy → corporate earnings → equity valuation
```

**Monitoring framework for the three major central banks:**

| Central Bank | Core Indicators | Forward Signals | Lagging Confirmation |
|------|---------|---------|---------|
| Federal Reserve (Fed) | FFR, dot plot, SEP | CME FedWatch probabilities | nonfarm payrolls / CPI / PCE |
| European Central Bank (ECB) | Main refinancing rate | Eurozone PMI, HICP | credit growth |
| Bank of Japan (BOJ) | YCC band, policy rate | JPY exchange rate, JGB yields | core CPI |

**Historical transmission of Fed hiking / cutting cycles to China A-shares (empirical):**
- Late in a Fed hiking cycle (the last 1-2 hikes), China A-shares often have already priced it in, and the average drawdown of the CSI 300 narrows to -3%
- In the 3 months after the first Fed cut, the CSI 300 has averaged +8.2% (mean of the 2001 / 2007 / 2019 cycles)
- But rate cuts do not automatically mean gains. In 2008, cuts came with recession and China A-shares still fell

### 2. Exchange Rate Forecasting Framework

**Three-layer model:**

| Model | Applicable Horizon | Core Variables | Accuracy |
|------|---------|---------|------|
| Purchasing Power Parity (PPP) | 3-5 years | CPI gap between two countries | Long-term anchor |
| Interest Parity (UIP/CIP) | 3-12 months | rate differential + forward premium/discount | Medium-term direction |
| BEER model | 1-3 years | terms of trade + net foreign inflows + productivity | Equilibrium estimate |

**USD/CNY practical checklist:**
- China-US 10Y spread > 0: appreciation pressure on the RMB (capital inflows)
- China-US 10Y spread < -150bp: rising depreciation pressure on the RMB
- Net FX settlement surplus / deficit: directly reflects conversion direction of corporates and households
- PBOC fixing vs market expectation: signal that the countercyclical factor has been activated

### 3. Geopolitical Risk Assessment

**Quantitative approach (proxy for the GPR index):**

```python
# Geopolitical risk proxy indicators
risk_indicators = {
    "vix": "Fear index > 25 = high risk",
    "gold_oil_ratio": "Gold / oil > 25 = rising risk aversion",
    "usd_index": "DXY jump > 2% / week = capital flowing back to USD",
    "credit_spread": "IG spread > 150bp = credit tightening",
    "em_spread": "EMBI spread widening > 50bp / month = emerging-market stress"
}
```

**Typical asset impacts of geopolitical events (historical averages):**
- Local conflicts: gold +3-5%, oil +5-15%, equities -2-5%, with impact lasting 1-4 weeks
- Trade friction: affected sectors -10-20%, beneficiary substitute sectors +5-10%, lasting 3-6 months
- Financial sanctions: sanctioned-country currency -10-30%, commodity supply side hit

### 4. Global Capital Flow Tracking

**Key data sources:**
- EPFR fund flows: weekly net inflows into global equity / bond funds
- Northbound flows (Shanghai-Shenzhen-Hong Kong Stock Connect): daily, with net buying > 10 billion RMB in a day as a strong signal
- US Treasury TIC data: monthly, showing changes in foreign holdings of Treasuries
- FX reserve changes: quarterly, indicating central-bank asset allocation direction

**Northbound flow signal rules (China A-share practice):**

| Signal | Condition | Meaning |
|------|------|------|
| Strong buy | Net buying for 5 consecutive days and cumulative amount > 20 billion RMB | Foreign investors are building positions trendwise |
| Weak buy | Single-day net buying > 8 billion RMB | Short-term sentiment is bullish |
| Warning | Net selling for 5 consecutive days and cumulative amount > 15 billion RMB | Foreign investors are reducing positions trendwise |
| Neutral | Daily net flow within ±3 billion RMB | No directional signal |

### 5. Dollar Cycle and Emerging Markets

**Four-stage dollar cycle model:**

```
Strong-dollar phase (DXY rising) → capital outflows from emerging markets → EM currency depreciation → EM equities and bonds both sell off
Weak-dollar phase (DXY falling) → capital flows back into EM → EM currency appreciation → EM assets outperform developed markets
```

**Practical mapping:**
- DXY > 105 and trending up: underweight emerging markets (China A-shares / Hong Kong stocks), overweight USD assets
- DXY < 100 and trending down: overweight emerging markets, underweight USD assets
- DXY in the 100-105 range: allocate selectively based on fundamentals

## Analysis Framework

### Steps for Building a Macro Dashboard

1. **Data collection**: rates (US 10Y / China 10Y government bonds), FX (DXY / USD-CNY), commodities (gold / oil / copper), capital flows (northbound / EPFR)
2. **Cycle positioning**: which stage are we in now: hiking / cutting / pause? Strong-dollar or weak-dollar cycle?
3. **Factor scoring**: score each macro factor from -2 to +2 (-2 = extremely bearish, +2 = extremely bullish)
4. **Asset mapping**: macro factor scores → recommended weights for major asset classes

### Example Macro Factor Scoring

```python
macro_factors = {
    "fed_policy": +1,      # Hiking pause, dovish tilt
    "cny_pressure": -1,    # RMB depreciation pressure
    "geopolitical": 0,     # Neutral geopolitical risk
    "northbound_flow": +2, # Persistent net northbound buying
    "usd_cycle": -1,       # Stronger USD
}
# Composite score = sum(values) / len(values) = +0.2 → neutral to mildly bullish
```

## Output Format

```
## Macro Analysis Report

### Cycle Positioning
- Federal Reserve: [late hiking / pause / early cutting]
- Dollar cycle: [strong / range-bound / weak]
- China monetary policy: [easing / neutral / tightening]

### Factor Scores (-2 ~ +2)
| Factor | Score | Basis |
|------|------|------|
| Central bank policy | +1 | Fed paused hiking and the market expects cuts this year |
| FX pressure | -1 | USD/CNY broke above 7.2 and FX settlement turned into deficit |
| Capital flows | +2 | Northbound net buying exceeded 20 billion RMB continuously |

### Asset Allocation Recommendations
- China A-shares: [overweight / neutral / underweight] — rationale
- Hong Kong stocks: [overweight / neutral / underweight] — rationale
- Gold: [overweight / neutral / underweight] — rationale
- US Treasuries: [overweight / neutral / underweight] — rationale

### Risk Warnings
- [specific risk events and potential impacts]
```

## Notes

- Macro analysis provides directional guidance, not precise timing. Leave timing to skills such as `technical-basic` or `volatility`
- Central-bank policy judgment should be based on official statements and meeting minutes. Do not over-interpret unofficial messages
- Exchange-rate forecasting has large errors. PPP deviations can persist for years, so use it for direction only, not exact levels
- Northbound flows contain noise (arbitrage / hedging), so persistence matters (at least 3 consecutive days in the same direction)
- Geopolitical shocks are usually short-lived (1-4 weeks) unless they change fundamentals (such as long-term sanctions or trade wars)
- This framework is not investment advice and is for research backtesting only
