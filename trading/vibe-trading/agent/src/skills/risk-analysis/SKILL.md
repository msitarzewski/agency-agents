---
name: risk-analysis
description: Risk measurement and stress testing — VaR/CVaR/max drawdown calculation, Monte Carlo simulation, extreme-value tail-risk analysis, and historical scenario stress testing.
category: analysis
---

# Risk Measurement and Stress Testing

## Overview

Systematic risk-measurement methodology covering VaR/CVaR calculation, Monte Carlo simulation, stress-test design, and tail-risk analysis. It provides risk evaluation for backtest results and risk-control constraints for asset allocation.

## Risk Measurement Methods

### 1. VaR (Value at Risk)

**Definition**: the maximum expected loss over a given horizon at a specified confidence level.

#### Three Calculation Methods

| Method | Formula / Steps | Advantages | Disadvantages |
|------|----------|------|------|
| Historical simulation | Sort historical returns and take the quantile | No distribution assumption | Depends on historical samples |
| Parametric (normal) | `VaR = μ - z_α × σ` | Easy to compute | Assumes a normal distribution |
| Monte Carlo | Simulate N paths and take the quantile | Flexible | Computationally intensive |

#### Historical Simulation Implementation

```python
import numpy as np
import pandas as pd

def historical_var(returns: pd.Series, confidence: float = 0.95, horizon: int = 1) -> float:
    """
    Args:
        returns: Daily return series
        confidence: Confidence level, commonly 0.95 or 0.99
        horizon: Holding period in days, default 1
    Returns:
        VaR value (positive means loss)
    """
    sorted_returns = returns.sort_values()
    index = int((1 - confidence) * len(sorted_returns))
    var_1d = -sorted_returns.iloc[index]
    return var_1d * np.sqrt(horizon)  # square-root-of-time rule
```

#### Parametric Implementation

```python
from scipy.stats import norm

def parametric_var(returns: pd.Series, confidence: float = 0.95, horizon: int = 1) -> float:
    mu = returns.mean()
    sigma = returns.std()
    z = norm.ppf(1 - confidence)
    var_1d = -(mu + z * sigma)
    return var_1d * np.sqrt(horizon)
```

### 2. CVaR / ES (Conditional VaR / Expected Shortfall)

**Definition**: the average loss beyond the VaR threshold, more conservative than VaR.

```python
def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """CVaR = the mean of all losses beyond VaR."""
    var = historical_var(returns, confidence)
    tail_losses = returns[returns < -var]
    return -tail_losses.mean() if len(tail_losses) > 0 else var
```

**VaR vs CVaR comparison**:

| Metric | VaR(95%) | CVaR(95%) | Meaning |
|------|----------|-----------|------|
| Typical value | -2.1% | -3.4% | CVaR is usually 1.3-1.8x VaR |
| Subadditivity | Not satisfied | Satisfied | CVaR can be used for portfolio risk decomposition |
| Regulation | Basel II | Basel III | Regulatory trend is shifting toward CVaR |

### 3. Maximum Drawdown Analysis

```python
def max_drawdown_analysis(equity: pd.Series) -> dict:
    """
    Args:
        equity: Net-value series
    Returns:
        dict: max_drawdown, peak_date, trough_date, recovery_date, duration
    """
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    max_dd = drawdown.min()
    trough_idx = drawdown.idxmin()
    peak_idx = equity[:trough_idx].idxmax()

    # Recovery date
    recovery = equity[trough_idx:][equity[trough_idx:] >= equity[peak_idx]]
    recovery_date = recovery.index[0] if len(recovery) > 0 else None

    return {
        'max_drawdown': max_dd,
        'peak_date': peak_idx,
        'trough_date': trough_idx,
        'recovery_date': recovery_date,
        'underwater_days': (trough_idx - peak_idx).days,
        'recovery_days': (recovery_date - trough_idx).days if recovery_date else None
    }
```

### 4. Monte Carlo Simulation

#### Geometric Brownian Motion (GBM)

```python
def monte_carlo_gbm(S0: float, mu: float, sigma: float,
                     T: int = 252, n_paths: int = 10000) -> np.ndarray:
    """
    Args:
        S0: Initial price
        mu: Annualized return
        sigma: Annualized volatility
        T: Number of simulation days
        n_paths: Number of paths
    Returns:
        Price matrix of shape (n_paths, T)
    """
    dt = 1 / 252
    Z = np.random.standard_normal((n_paths, T))
    log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    prices = S0 * np.exp(np.cumsum(log_returns, axis=1))
    return prices
```

#### Simulation Result Analysis

```python
def analyze_mc_results(paths: np.ndarray, confidence: float = 0.95) -> dict:
    final_prices = paths[:, -1]
    returns = final_prices / paths[:, 0] - 1

    return {
        'mean_return': np.mean(returns),
        'median_return': np.median(returns),
        'std_return': np.std(returns),
        'var': -np.percentile(returns, (1 - confidence) * 100),
        'cvar': -np.mean(returns[returns < -np.percentile(returns, (1-confidence)*100)]),
        'prob_loss': np.mean(returns < 0),
        'worst_5pct': np.percentile(returns, 5),
        'best_5pct': np.percentile(returns, 95),
    }
```

## Stress-Testing Framework

### Historical Scenario Stress Tests

| Scenario | Period | China A-share Drawdown | US Equity Drawdown | BTC Drawdown | 10Y Government Bonds |
|------|--------|---------|---------|---------|---------|
| 2008 financial crisis | 2008.01-2008.10 | -65% | -50% | N/A | yield ↓ 100bp |
| 2015 China equity crash | 2015.06-2015.08 | -45% | -10% | -20% | yield ↓ 50bp |
| 2018 trade war | 2018.01-2018.12 | -25% | -20% | -80% | yield ↓ 30bp |
| 2020 COVID shock | 2020.01-2020.03 | -15% | -35% | -50% | yield ↓ 80bp |
| 2022 hiking cycle | 2022.01-2022.10 | -20% | -25% | -65% | yield ↑ 200bp |

### Hypothetical Scenario Design

```python
STRESS_SCENARIOS = {
    'rate_shock_up_100bp': {
        'equity': -0.10,    # equities down 10%
        'bond_10y': -0.08,  # 10-year bonds down 8%
        'bond_2y': -0.02,   # short bonds down 2%
        'gold': +0.05,      # gold up 5%
        'btc': -0.15,       # BTC down 15%
    },
    'credit_crisis': {
        'equity': -0.25,
        'bond_10y': +0.05,  # government bonds act as a safe haven
        'credit_bond': -0.15,
        'gold': +0.10,
        'btc': -0.30,
    },
    'liquidity_dry_up': {
        'equity': -0.20,
        'bond_10y': -0.05,  # when liquidity is poor, everything falls
        'gold': -0.05,
        'btc': -0.40,
        'cash': 0.0,
    },
    'geopolitical_conflict': {
        'equity': -0.15,
        'bond_10y': +0.03,
        'gold': +0.15,
        'oil': +0.30,
        'btc': -0.20,
    },
}
```

### Stress-Test Implementation Steps

1. **Select a scenario**: either historical or hypothetical
2. **Apply shocks**: multiply scenario shocks by the current positions
3. **Compute portfolio loss**: `portfolio_loss = Σ(weight_i × shock_i × position_i)`
4. **Assess adequacy**: compare loss vs risk budget and whether stop-loss thresholds are triggered

## Tail-Risk Analysis (Extreme Value Theory, EVT)

### POT Method (Peaks Over Threshold)

```python
from scipy.stats import genpareto

def fit_gpd_tail(returns: pd.Series, threshold_pct: float = 5.0) -> dict:
    """
    Fit the tail with a generalized Pareto distribution.
    Args:
        returns: Daily returns
        threshold_pct: Threshold percentile (take the worst X%)
    """
    threshold = np.percentile(returns, threshold_pct)
    exceedances = threshold - returns[returns < threshold]  # make positive

    # Fit GPD
    shape, loc, scale = genpareto.fit(exceedances)

    return {
        'threshold': threshold,
        'n_exceedances': len(exceedances),
        'shape_xi': shape,      # ξ>0 fat tail, ξ=0 exponential tail, ξ<0 bounded tail
        'scale_sigma': scale,
        'tail_type': 'fat tail (dangerous)' if shape > 0 else 'thin tail (safer)',
    }
```

### Tail-Risk Metrics

| Metric | Calculation | Meaning |
|------|------|------|
| Kurtosis | `returns.kurtosis()` | >3 indicates fat tails; China A-shares are often in the 4-8 range |
| Skewness | `returns.skew()` | <0 means left-skewed (large drops are more common than large rallies) |
| Tail ratio | worst 5% / best 5% | >1 means larger downside risk |
| Hill estimator | Tail index | `α<2` implies extremely fat tails |

## Analysis Framework

### Input Requirements

```
Required:
- Return series (daily or higher frequency) or net-value series
- Portfolio weights (if it is a portfolio)

Optional:
- Benchmark returns (for relative risk analysis)
- Risk budget / constraint settings
```

### Analysis Steps

1. **Data preprocessing**: compute returns, check missing values, and handle outliers
2. **Descriptive statistics**: mean / volatility / skewness / kurtosis / maximum drawdown
3. **VaR/CVaR calculation**: compare three methods at both 95% and 99% confidence levels
4. **Monte Carlo simulation**: 10,000 paths, output distribution statistics and VaR
5. **Stress testing**: at least 3 historical scenarios + 2 hypothetical scenarios
6. **Tail analysis**: fit GPD and determine tail type
7. **Risk-control recommendations**: provide concrete recommendations based on the results

## Output Format

```markdown
## Risk Analysis Report

### Core Risk Metrics
| Metric | Value |
|------|-----|
| Daily volatility | 1.85% |
| Annualized volatility | 29.3% |
| Maximum drawdown | -32.5% (2024.09.15 → 2024.11.20) |
| VaR(95%, 1D) | -2.8% |
| CVaR(95%, 1D) | -4.2% |
| Skewness | -0.45 |
| Kurtosis | 5.2 (fat tail) |

### Stress-Test Results
| Scenario | Portfolio Loss | Stop Triggered |
|------|---------|----------|
| 2020 COVID replay | -18.5% | No |
| Rates +100bp | -12.3% | No |
| Liquidity dry-up | -28.7% | Yes |

### Monte Carlo Simulation (252 days, 10000 paths)
| Statistic | Value |
|------|-----|
| Expected return | +8.2% |
| Loss probability | 35% |
| Worst 5% scenario | -22.4% |

### Risk-Control Recommendations
1. Recommend setting a portfolio stop-loss at -15%
2. Tail risk is elevated; consider allocating 5% to gold as a hedge
3. Correlations rise in stressed markets, so diversification benefits will be discounted
```

## Notes

1. **VaR is not the maximum loss**: VaR only says "with 95% probability, losses will not exceed X"; the remaining 5% can be far worse
2. **Normality assumption is dangerous**: financial returns are almost always fat-tailed, so parametric VaR underestimates risk
3. **History does not equal the future**: historical simulation fails when structural breaks occur (for example, the first negative oil price)
4. **Correlation is unstable**: correlation matrices observed in normal markets can collapse in crises (correlations trend toward 1)
5. **Monte Carlo seed**: set a random seed for reproducibility, and use at least 10,000 paths for stability
6. **Holding-period scaling**: the square-root-of-time rule only applies under i.i.d. returns; it becomes inaccurate under autocorrelation
7. **Risk in backtests**: `metrics.csv` already includes `max_drawdown` and `sharpe`; this skill provides deeper analysis
