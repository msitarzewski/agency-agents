---
name: options-advanced
description: "Advanced options strategies: volatility-surface modeling (SABR / Local Vol), dynamic Greeks rebalancing, calendar spreads, volatility arbitrage and skew trading, and option market-making basics."
category: asset-class
---

# Advanced Options Strategies

## Overview

Go beyond basic option strategies (`covered call` / `protective put`) and focus on trading opportunities along the volatility dimension. Core idea: option price = intrinsic value + time value, and advanced trading essentially trades the volatility expectations embedded behind that time value.

Applicable scenarios:
- Identifying arbitrage opportunities when the volatility surface is abnormal (`skew` / `term structure`)
- Fine-grained management of portfolio Greeks exposures (not just Delta hedging)
- Building structured strategies across maturities and strikes
- Practical application in 50ETF / 300ETF / commodity options

## Core Concepts

### Volatility Surface

Three-dimensional structure: strike × expiry × implied volatility.

**Key dimensions**:
| Dimension | Meaning | Typical Shape |
|------|------|----------|
| Smile / Skew | IV across strikes for the same expiry | China A-shares: left-skewed (`put IV > call IV`) |
| Term Structure | IV across expiries for the same strike | Normal case: near-month IV < far-month IV |
| Surface dynamics | Parallel or nonlinear movement of the entire surface | In panic, the whole surface lifts, and near-month IV lifts faster |

**SABR model parameters**:
```
α (alpha): initial volatility level, around 0.2-0.5
β (beta): CEV exponent, equities usually use 0.5-1.0
ρ (rho): correlation between volatility and the underlying, usually -0.3 to -0.7 in China A-shares (negative = left skew)
ν (nu): volatility of volatility (vol of vol), around 0.3-0.8
```

**Local Vol vs SABR**:
- Local Vol (Dupire): backed out from market prices, exact fit but unstable extrapolation
- SABR: parameterized model, 4 parameters capture surface dynamics and extrapolate more reasonably

### Dynamic Greeks Management

**First-order Greeks**:
| Greek | Meaning | Management Approach |
|-------|------|----------|
| Delta (Δ) | Sensitivity to underlying price | Hedge frequency: daily for ATM, every 2-3 days for OTM |
| Vega (ν) | Sensitivity to IV | Calendar spreads can isolate Vega exposure |
| Theta (Θ) | Time decay | Short-option strategies are naturally positive Theta, but watch Gamma risk |
| Rho (ρ) | Sensitivity to rates | Relevant for long-dated options, usually ignorable for short-dated options |

**Second-order Greeks**:
| Greek | Meaning | Key Scenario |
|-------|------|----------|
| Gamma (Γ) | Rate of change of Delta | Highest near ATM and spikes before expiry |
| Vanna | Sensitivity of Delta to IV | Core Greek for skew trading |
| Volga / Vomma | Sensitivity of Vega to IV | Important when volatility moves sharply |

**Delta hedge frequency decision**:
```
Hedging cost = trading frequency × slippage per rebalance
Unhedged risk = Gamma exposure × underlying volatility²
Optimal frequency (Zakamouline criterion):
  Trigger hedge when Gamma × S² × σ² × Δt > 2 × transaction_cost
Practical rule: ATM Gamma is large -> hedge daily; OTM -> hedge weekly or on threshold triggers
```

## Analysis Framework

### 1. Calendar Spread

**Principle**: sell the near-month option and buy the far-month option at the same strike, profiting from faster near-month Theta decay.

**Entry conditions**:
- Normal term structure (`near-month IV ≤ far-month IV`)
- Expect the underlying to stay in a narrow range
- Open the position 20-30 days before near-month expiry

**50ETF example**:
```
Underlying: 50ETF current price 2.80
Sell: 50ETF near-month C2800  IV=18%, collect premium 0.045
Buy: 50ETF far-month C2800   IV=20%, pay premium 0.082
Net debit: 0.037 (max loss)
Breakeven: profit if the underlying stays in the 2.76-2.84 range at near-month expiry
Max profit: when near-month expires with the underlying right at 2.80, roughly 0.045 minus the time-decay differential
```

**Risk-control points**:
- Large breakout in the underlying → stop loss (if loss exceeds 50% of net debit)
- Near-month IV suddenly rises above far-month IV (term-structure inversion) → close position

### 2. Volatility Arbitrage

**Long Gamma strategy** (buy volatility):
```
Scenario: realized volatility is expected to exceed implied volatility
Trade: buy ATM straddle + Delta hedge
Profit source: Gamma-scalping gains > Theta decay
Key metric:
  Breakeven volatility = IV + Theta/Gamma cost
  Example in 300ETF: buy straddle at IV=16%; if realized volatility >18%, the trade is profitable
```

**Short Gamma strategy** (sell volatility):
```
Scenario: realized volatility is expected to stay below implied volatility
Trade: sell ATM straddle + Delta hedge
Profit source: Theta income > hedging loss
Risk control: set max loss = 2x premium received, close when hit
```

### 3. Skew Trade

**Risk Reversal**:
```
Scenario: skew is too steep (put IV excessively high relative to call IV)
Trade: sell OTM put + buy OTM call (zero-cost or slight net credit)
Exposure: long skew (profit if skew mean-reverts)
50ETF example:
  Sell P2700 IV=22%  collect 0.025
  Buy C2900 IV=16%   pay 0.018
  Net credit 0.007, profiting from skew mean reversion
```

**Butterfly skew trade**:
```
Scenario: localized skew abnormality (IV deviation at a particular strike)
Trade: build a butterfly centered on the abnormal strike
  If IV is too high -> sell that strike (middle leg of the butterfly)
  If IV is too low -> buy that strike
```

### 4. Option Market-Making Basics

**Quoting strategy**:
- Bid-ask spread = `f(Gamma risk, inventory skew, market volatility)`
- Narrow spreads attract flow; wider spreads protect risk
- Inventory-skew management: if Delta exceeds the limit, tilt quotes to induce the other side to offset inventory

**Inventory management**:
```
Delta limit: ±500 underlying-equivalent lots
Gamma limit: daily Gamma PnL should not exceed 2% of account equity
Vega limit: PnL from a 1% IV move should not exceed 1% of account equity
When over the limit: hedge in the market first, adjust quotes second
```

## Output Format

Volatility analysis report:
```
=== Volatility Surface Analysis ===
Underlying: 50ETF  Current price: 2.80
ATM IV: 18.5%  Historical percentile: 35% (relatively low)
Skew (25D): -3.2% (put IV is 3.2% higher than call IV)  Historical percentile: 70% (relatively steep)
Term Structure: normal (near-month 17.8% < far-month 19.2%)

=== Strategy Recommendation ===
Opportunity: steep skew + low IV
Strategy: Risk Reversal (sell put / buy call) + Calendar Spread
Expectation: skew mean reversion + mild IV rise
Risk control: keep Delta neutral, keep Gamma within ±200 lots

=== Greeks Monitoring ===
Portfolio Delta: +15 (neutral)
Portfolio Gamma: -180 (short Gamma, watch gap risk)
Portfolio Vega: +3200 (long Vega, benefits from higher IV)
Portfolio Theta: -450 / day
```

## Notes

1. **China A-share option characteristics**: liquidity in 50ETF / 300ETF options is concentrated in near-month ATM ± 3 strikes; deep OTM and far-month options are illiquid and have large slippage
2. **Margin management**: short-option margin changes dynamically with the underlying; keep >30% buffer to avoid margin calls
3. **Expiry-week effect**: Gamma rises sharply during the week before expiry, Pin Risk increases, and short-option traders should reduce size early
4. **Market-making barrier**: real market making requires high-frequency infrastructure, low latency, and professional risk controls; retail traders should not attempt pure market making
5. **SABR calibration**: calibrate parameters daily after the close with market data, then use prior-day parameters plus real-time adjustment at the open
6. **Gamma scalping PnL**: actual profit = `0.5 × Gamma × (RV² - IV²) × S² × T`; realized volatility must exceed IV by a meaningful margin to cover transaction costs

## Dependencies

```bash
pip install pandas numpy scipy
```
