---
name: asset-allocation
description: Asset allocation theory and optimizer usage — MPT / Black-Litterman / risk budgeting / all-weather strategy, including guides for 4 optimizers and rebalancing rules.
category: asset-class
---

# Asset Allocation and Portfolio Optimization

## Overview

From asset allocation theory to practical implementation, this skill covers classical frameworks (MPT, BL, risk budgeting, all-weather) and the usage of the four optimizers built into this system. The output can be written directly into `config.json`.

## Asset Allocation Theory

### 1. Modern Portfolio Theory (MPT, Markowitz)

**Core idea**: maximize expected return for a given level of risk (the efficient frontier).

```
Optimization problem:
min  w'Σw              (portfolio variance)
s.t. w'μ = target_return
     Σw = 1
     w ≥ 0              (no shorting)
```

| Advantages | Disadvantages |
|------|------|
| Mathematically rigorous | Extremely sensitive to inputs (garbage in, garbage out) |
| Efficient frontier is visualizable | Concentrated-allocation problem (often produces extreme weights) |
| Foundational framework | Assumes normality and ignores fat tails |

**Practical advice**: do not use raw MPT directly. Add constraints (upper/lower bounds, sector limits) or use a regularized version.

### 2. Black-Litterman Model

**Core idea**: start from market equilibrium and incorporate investor views.

```
Steps:
1. Reverse-imply market equilibrium returns: π = δΣw_mkt
2. Build the view matrices: P (selection matrix), Q (view returns), Ω (view uncertainty)
3. Blend the posterior: μ_BL = [(τΣ)^-1 + P'Ω^-1 P]^-1 [(τΣ)^-1 π + P'Ω^-1 Q]
4. Run Markowitz optimization using posterior μ_BL
```

**Example views**:
- Absolute view: "China A-shares will return 10% over the next year"  → `P=[1,0,0], Q=[0.10]`
- Relative view: "China A-shares will outperform US equities by 5%"   → `P=[1,-1,0], Q=[0.05]`

**Parameter guidance**:
- `τ` (uncertainty scaling): `0.025-0.05`
- `Ω`: set according to view confidence, where higher confidence = smaller variance

### 3. Risk Budgeting

**Core idea**: allocate by risk contribution rather than by capital share.

```
Risk contribution: RC_i = w_i × (Σw)_i / σ_p
Target: RC_i / σ_p = budget_i  (for all i)
```

| Strategy | Risk Budget | Best Use Case |
|------|---------|---------|
| Equal risk contribution | Each asset 1/N | When you do not know which asset is best |
| Equity-tilted risk budget | Stocks 60%, bonds 30%, commodities 10% | When you want equities to contribute more risk |
| Dynamic risk budget | Adjust dynamically by signal strength | When you have market-timing ability |

### 4. All-Weather Strategy

**Bridgewater framework**: allocate risk equally across economic environments.

```
Economic environment   Asset allocation
─────────              ─────────
Growth rising          Equities + commodities + corporate bonds
Growth falling         Government bonds + inflation-protected bonds
Inflation rising       Commodities + inflation-protected bonds + EM debt
Inflation falling      Equities + government bonds

Simplified allocation example for China-focused portfolios:
- 30% CSI 300 / CSI 500
- 40% government bonds / credit bonds
- 15% gold
- 15% commodities / REITs
```

## Guide to the 4 Optimizers

### Overview of the Built-In Optimizers

Configure them in `config.json` through `optimizer` and `optimizer_params`:

| optimizer | Display Name | Core Idea | Best Use Case |
|-----------|--------|---------|---------|
| `equal_volatility` | Equal Volatility | Allocate weights by inverse volatility | Simple and effective baseline |
| `risk_parity` | Risk Parity | Equalize risk contribution while accounting for correlation | Long-term robust allocation |
| `mean_variance` | Mean-Variance | Maximize Sharpe ratio or minimize variance | When return forecasts are available |
| `max_diversification` | Maximum Diversification | Maximize the diversification ratio | When pursuing a low-correlation portfolio |

### 1. `equal_volatility`

```json
{
  "optimizer": "equal_volatility",
  "optimizer_params": {
    "lookback": 60
  }
}
```

**Principle**: `w_i = (1/σ_i) / Σ(1/σ_j)`

| Parameter | Default | Description |
|------|--------|------|
| lookback | 60 | Volatility calculation window (trading days) |

**Advantages**: simple and fast, no return forecast required, no correlation matrix required.  
**Disadvantages**: ignores cross-asset correlation.

### 2. `risk_parity`

```json
{
  "optimizer": "risk_parity",
  "optimizer_params": {
    "lookback": 60
  }
}
```

**Principle**: solve for weights such that each asset contributes the same amount of risk.

| Parameter | Default | Description |
|------|--------|------|
| lookback | 60 | Covariance-matrix estimation window |

**Advantages**: accounts for correlation, spreads risk more evenly, and is robust over long horizons.  
**Disadvantages**: requires iterative solving and is sensitive to covariance estimates.

### 3. `mean_variance`

```json
{
  "optimizer": "mean_variance",
  "optimizer_params": {
    "lookback": 60,
    "risk_free": 0.0
  }
}
```

**Principle**: Markowitz optimization that maximizes the Sharpe ratio.

| Parameter | Default | Description |
|------|--------|------|
| lookback | 60 | Window for estimating means and covariances |
| risk_free | 0.0 | Risk-free rate (annualized) |

**Advantages**: theoretically optimal (if inputs are accurate).  
**Disadvantages**: extremely sensitive to inputs, prone to extreme weights, and often performs poorly out of sample.  
**Recommendation**: do not make `lookback` too short (`<30` easily overfits), and add upper/lower weight constraints.

### 4. `max_diversification`

```json
{
  "optimizer": "max_diversification",
  "optimizer_params": {
    "lookback": 60
  }
}
```

**Principle**: maximize `DR = (w'σ) / σ_p` (the diversification ratio).

| Parameter | Default | Description |
|------|--------|------|
| lookback | 60 | Calculation window |

**Advantages**: does not require return forecasts and seeks true diversification.  
**Disadvantages**: effectiveness is limited in highly correlated environments.

### Optimizer Selection Decision Tree

```
Do you have return forecasts?
├── Yes → mean_variance (remember to add constraints)
└── No → Do you need to account for correlation?
    ├── Yes → risk_parity (recommended default)
    └── No → Are volatility differences across assets large?
        ├── Yes → equal_volatility
        └── No → max_diversification
```

## Rebalancing Strategy

### Three Rebalancing Triggers

| Method | Trigger Condition | Advantages | Disadvantages |
|------|---------|------|------|
| Periodic rebalancing | Fixed monthly / quarterly date | Simple, predictable trading cost | May miss or delay adjustments |
| Threshold trigger | Deviation from target weight > X% | Trades only when needed | Frequent trading in high-volatility markets |
| Volatility trigger | VIX / volatility breaks a threshold | Adapts to market regime | Parameter selection is difficult |

### Suggested Rebalancing Frequency

| Asset Class | Suggested Frequency | Threshold |
|---------|---------|------|
| Equity portfolio | Monthly | ±5% |
| Stock-bond mix | Quarterly | ±10% |
| Global macro | Quarterly / semiannual | ±10% |
| Cryptocurrency | Weekly / biweekly | ±15% (high volatility) |

### Rebalancing in Backtests

Implement rebalancing logic in `signal_engine.py`:

```python
# Periodic rebalancing example (every 20 trading days)
if bar_count % rebalance_freq == 0:
    # Recompute weights
    new_weights = calculate_target_weights(data_map)
    for code, weight in new_weights.items():
        signals[code].iloc[i] = weight
```

## Cross-Asset Correlation Analysis

### Typical Correlation Matrix (China-Focused Portfolio Example)

| | CSI 300 | CSI 500 | Government Bonds | Gold | BTC |
|--|--------|--------|------|------|-----|
| CSI 300 | 1.00 | 0.85 | -0.15 | 0.05 | 0.10 |
| CSI 500 | 0.85 | 1.00 | -0.10 | 0.03 | 0.12 |
| Government Bonds | -0.15 | -0.10 | 1.00 | 0.20 | -0.05 |
| Gold | 0.05 | 0.03 | 0.20 | 1.00 | 0.15 |
| BTC | 0.10 | 0.12 | -0.05 | 0.15 | 1.00 |

**Key patterns**:
- Negative stock-bond correlation is the foundation of allocation (but it does not always hold; in 2022 both stocks and bonds sold off)
- Gold has low correlation with equities and serves as a hedge
- BTC's correlation with traditional assets is unstable and tends to become positive in crises
- Large-cap versus small-cap China A-shares have high correlation (`0.85`), so diversification benefits are limited

## Output Format

```markdown
## Asset Allocation Recommendation

### Allocation Plan
| Asset | Weight | Risk Contribution | Expected Return (Annualized) |
|------|------|---------|--------------|
| CSI 300 | 30% | 45% | 8% |
| Government Bond ETF | 40% | 15% | 3% |
| Gold | 15% | 20% | 5% |
| BTC | 15% | 20% | 15% |

### Optimizer Configuration
```json
{
  "optimizer": "risk_parity",
  "optimizer_params": {"lookback": 60}
}
```

### Expected Risk / Return
| Metric | Value |
|------|-----|
| Expected annualized return | 7.2% |
| Expected annualized volatility | 8.5% |
| Expected Sharpe | 0.85 |
| Expected maximum drawdown | -12% |

### Rebalancing Rules
- Frequency: quarterly (first trading day of March / June / September / December)
- Threshold: trigger when any asset deviates from target by ±10%
- Cost: estimated annual trading cost 0.15%
```

## Notes

1. **The optimizer needs enough instruments**: at least 3 instruments are needed for meaningful optimization; with 2 instruments, `equal_volatility` is usually enough
2. **`lookback` window**: too short (`<20`) is noisy, too long (`>120`) reacts slowly, and 60 is a reasonable default
3. **`mean_variance` trap**: it is the easiest to overfit, and out-of-sample Sharpe is often cut by half or more
4. **Rebalancing cost**: frequent rebalancing eats into returns; for China A-share portfolios, stamp duty of 0.05% plus commissions is material
5. **Cross-market allocation**: use `"source": "auto"` in `config.json`, and let `codes` mix instruments from different markets
6. **Leverage constraint**: the sum of weights must be ≤ 1.0, and leverage is not allowed unless explicitly specified
7. **Survivorship bias**: historical correlations may be distorted by delistings and new listings
