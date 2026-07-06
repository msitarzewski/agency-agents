---
name: options-payoff
description: "Option P&L analysis methodology: payoff diagrams, breakeven calculation, multi-leg strategy visualization, and Greeks-based scenario analysis."
category: asset-class
---

# Options Payoff — Option P&L Analysis Methodology

## Overview

This skill is designed for option strategy analysis scenarios within the Vibe-Trading quantitative framework, covering:
- P&L curve generation for single-leg and multi-leg option portfolios
- Black-Scholes pricing and Greeks calculation
- Implied volatility inversion
- Strategy selection decision support

**Constraint**: For research and backtesting only. Do not output live trading instructions, in line with the project's guardrails.

---

## 1. Supported Strategy Types

### 1.1 Single-Leg Strategies

| Strategy | Bias | Premium | Max Profit | Max Loss |
|------|------|--------|----------|----------|
| Long Call | Bullish | Paid | Unlimited | Premium |
| Long Put | Bearish | Paid | Strike - premium | Premium |
| Short Call | Neutral / mildly bearish | Received | Premium | Unlimited |
| Short Put | Neutral / mildly bullish | Received | Premium | Strike - premium |

### 1.2 Vertical Spreads

| Strategy | Structure | Market View | Net Premium |
|------|------|----------|----------|
| Bull Call Spread | Long Call (lower K) + Short Call (higher K) | Moderately bullish | Net debit |
| Bear Put Spread | Long Put (higher K) + Short Put (lower K) | Moderately bearish | Net debit |
| Bull Put Spread | Short Put (higher K) + Long Put (lower K) | Moderately bullish | Net credit |
| Bear Call Spread | Short Call (lower K) + Long Call (higher K) | Moderately bearish | Net credit |

### 1.3 Straddles / Strangles (Volatility Strategies)

| Strategy | Structure | Market View |
|------|------|----------|
| Long Straddle | Long Call (ATM) + Long Put (ATM) | Large move up or down, low volatility |
| Short Straddle | Short Call (ATM) + Short Put (ATM) | Range-bound market, high volatility |
| Long Strangle | Long Call (OTM) + Long Put (OTM) | Large move, lower cost than a straddle |
| Short Strangle | Short Call (OTM) + Short Put (OTM) | Tight range, collect two-sided premium |

### 1.4 Butterflies / Iron Butterflies

| Strategy | Structure | Feature |
|------|------|------|
| Long Butterfly (Call) | Long Call (K1) + 2× Short Call (K2) + Long Call (K3) | Low-cost bet that the underlying expires near K2 |
| Long Butterfly (Put) | Long Put (K3) + 2× Short Put (K2) + Long Put (K1) | Same logic, built with puts |
| Iron Butterfly | Short Call (K2) + Short Put (K2) + Long Call (K3) + Long Put (K1) | Net credit, max profit at K2 |

### 1.5 Condors / Iron Condors

| Strategy | Structure | Feature |
|------|------|------|
| Long Condor (Call) | Long Call (K1) + Short Call (K2) + Short Call (K3) + Long Call (K4) | Bet that the underlying stays between K2 and K3 |
| Iron Condor | Short Put (K2) + Long Put (K1) + Short Call (K3) + Long Call (K4) | Most common neutral strategy with capped risk on both sides |

Here K1 < K2 < K3 < K4, and K2 / K3 are usually OTM.

### 1.6 Calendar Spreads (Time Spreads)

| Strategy | Structure | Market View |
|------|------|----------|
| Calendar Spread | Short near-month Call/Put (K) + Long far-month Call/Put (K) | Short-term range-bound market + rising forward volatility |
| Diagonal Spread | Short near-month Call/Put (K1) + Long far-month Call/Put (K2) | Calendar spread with mild directional bias |

Calendar spreads profit because near-month Theta decay is faster than far-month Theta decay.

### 1.7 Ratio Spreads

| Strategy | Structure | Feature |
|------|------|------|
| Ratio Call Spread | Long 1× Call (K1) + Short N× Call (K2), N>1 | Limited upside profit, losses if the upside move becomes extreme |
| Ratio Put Spread | Long 1× Put (K2) + Short N× Put (K1) | Limited downside profit, losses if the downside move becomes extreme |
| Call Back Spread | Short 1× Call (K1) + Long N× Call (K2), N>1 | Profits from extreme upside, loses on a modest rally |
| Put Back Spread | Short 1× Put (K2) + Long N× Put (K1), N>1 | Profits from extreme downside, loses on a mild decline |

### 1.8 Protective / Hedging Strategies

| Strategy | Structure | Use Case |
|------|------|------|
| Covered Call | Long underlying + Short Call (K) | Generate income on an existing position, give up gains above K |
| Protective Put | Long underlying + Long Put (K) | Downside protection on an existing position, pay an insurance premium |
| Collar | Long underlying + Long Put (K1) + Short Call (K2) | Lock the position into a zero-cost / low-cost range |

---

## 2. Black-Scholes Pricing Model

### 2.1 Core Assumptions

- The underlying price follows geometric Brownian motion (lognormal distribution)
- Risk-free rate `r` is constant
- Volatility `σ` is constant (historical or implied)
- No dividends, or adjust with a continuous dividend yield `q`
- European options only (exercise at expiration)

### 2.2 Full Formula

```
S  = current underlying price
K  = strike price
T  = time to expiration (years)
r  = risk-free rate (annualized continuous compounding)
q  = continuous dividend yield (commonly used for China A-share / index options)
σ  = annualized volatility
N  = standard normal CDF

d1 = [ln(S/K) + (r - q + σ²/2) × T] / (σ × √T)
d2 = d1 - σ × √T

Call = S × e^(-qT) × N(d1) - K × e^(-rT) × N(d2)
Put  = K × e^(-rT) × N(-d2) - S × e^(-qT) × N(-d1)
```

### 2.3 Put-Call Parity

```
Call - Put = S × e^(-qT) - K × e^(-rT)
```

Use this to verify pricing consistency and detect arbitrage. When dividends exist, replace `S` with `S × e^(-qT)`.

### 2.4 Greeks Calculation

#### Delta (Price Sensitivity)
```
Delta(Call) = e^(-qT) × N(d1)
Delta(Put)  = e^(-qT) × (N(d1) - 1)
```
- Range: Call [0, 1], Put [-1, 0]
- ATM ≈ ±0.5, deep ITM → ±1, deep OTM → 0

#### Gamma (Rate of Change of Delta)
```
Gamma = e^(-qT) × N'(d1) / (S × σ × √T)

N'(x) = (1/√(2π)) × e^(-x²/2)  [standard normal PDF]
```
- Calls and puts have the same Gamma
- Gamma is highest near ATM and explodes as expiration approaches

#### Theta (Time Decay, per day)
```
Theta(Call) = [-S × e^(-qT) × N'(d1) × σ / (2√T)
               - r × K × e^(-rT) × N(d2)
               + q × S × e^(-qT) × N(d1)] / 365

Theta(Put)  = [-S × e^(-qT) × N'(d1) × σ / (2√T)
               + r × K × e^(-rT) × N(-d2)
               - q × S × e^(-qT) × N(-d1)] / 365
```
- Usually negative for option holders
- ATM options near expiration have the largest Theta magnitude, which benefits option sellers the most

#### Vega (Volatility Sensitivity, per 1% vol change)
```
Vega = S × e^(-qT) × N'(d1) × √T / 100
```
- Calls and puts have the same Vega
- ATM Vega is the largest, and Vega approaches 0 at expiration

#### Rho (Interest Rate Sensitivity, per 1% rate change)
```
Rho(Call) = K × T × e^(-rT) × N(d2) / 100
Rho(Put)  = -K × T × e^(-rT) × N(-d2) / 100
```
- The rate effect is usually small and often negligible for short-dated options

### 2.5 Implied Volatility Inversion (Newton-Raphson)

Given a market price `P_market`, solve for `σ` such that `BS(σ) = P_market`:

```
Iteration:
σ_{n+1} = σ_n - [BS(σ_n) - P_market] / Vega(σ_n)

Stopping condition: |BS(σ_n) - P_market| < 1e-6

Initial guess:
σ_0 = √(2π/T) × P_market/S  (Brenner-Subrahmanyam approximation)

Notes:
- If Vega is close to 0 (deep OTM / ITM), switch to bisection
- If the iteration does not converge (>100 rounds), return NaN and raise a warning
- IV > 500% is usually an outlier and should be filtered
```

---

## 3. Payoff Diagram Analysis

### 3.1 Expiry Payoff Curve

**Calculation logic**:
```
For each leg i (Call/Put, Long/Short, strike K_i, quantity n_i):
  Payoff_i(S_T) = n_i × direction_i × max(0, S_T - K_i)  # Call
  Payoff_i(S_T) = n_i × direction_i × max(0, K_i - S_T)  # Put

Where direction = +1 (Long) / -1 (Short)

Portfolio payoff = Σ Payoff_i - net premium cost
  (paid premium is positive, received premium is negative)
```

**X-axis range**: `[min(K) × 0.7, max(K) × 1.3]`, step size 0.5 or 1

### 3.2 Theoretical Value Curve (Current Black-Scholes Pricing)

For each underlying price `S`, hold `T`, `r`, and `σ` constant and compute current theoretical PnL using the Black-Scholes formula:
```
TheoValue(S) = Σ n_i × direction_i × BS_price(S, K_i, T, r, σ, type_i) - net premium cost
```

The gap between the theoretical value curve and the expiry curve equals the remaining time value.

### 3.3 Break-Even Points

Numerically solve for the roots of `Payoff(S_T) = 0`:
- Use `scipy.optimize.brentq` to solve within adjacent intervals where the sign changes
- Single-leg strategies:
  - Long Call BEP = K + premium
  - Long Put BEP = K - premium
  - Short Call BEP = K + premium received
  - Short Put BEP = K - premium received
- Multi-leg strategies: solve numerically, possibly resulting in 0 to 2 BEPs

### 3.4 Max Profit / Max Loss

```python
max_profit = max(payoff_curve)    # If inf, label as "Unlimited"
max_loss   = min(payoff_curve)    # If -inf, label as "Unlimited"

# Corresponding underlying price region
profit_range = S_range[payoff_curve > 0]
```

### 3.5 P&L Under Different Volatility Scenarios

Generate a `σ` scenario matrix using `current IV × [0.5, 0.75, 1.0, 1.25, 1.5]`.
Plot one theoretical value curve for each `σ` and distinguish them by color to observe Vega sensitivity.

---

## 4. Python Code Templates

### 4.1 Black-Scholes Pricing Functions

```python
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Literal

def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
    q: float = 0.0,
) -> float:
    """Black-Scholes option pricing.

    Args:
        S: Current underlying price
        K: Strike price
        T: Time to expiration in years
        r: Risk-free rate in annualized continuous compounding, e.g. 0.03
        sigma: Annualized volatility, e.g. 0.20
        option_type: "call" or "put"
        q: Continuous dividend yield, defaults to 0

    Returns:
        Theoretical option price

    Raises:
        ValueError: If sigma <= 0
    """
    if T <= 0:
        # After expiration, return intrinsic value directly.
        if option_type == "call":
            return max(0.0, S - K)
        return max(0.0, K - S)
    if sigma <= 0:
        raise ValueError(f"sigma must be > 0, got {sigma}")

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    return float(price)


def bs_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"],
    q: float = 0.0,
) -> dict:
    """Calculate the five major Greeks under the Black-Scholes model.

    Returns:
        A dict with keys: delta, gamma, theta, vega, rho.
        Theta and Vega are already converted to per-day and per-1% units.
    """
    if T <= 1e-6:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    n_prime_d1 = norm.pdf(d1)
    exp_qt = np.exp(-q * T)
    exp_rt = np.exp(-r * T)

    if option_type == "call":
        delta = exp_qt * norm.cdf(d1)
        rho = K * T * exp_rt * norm.cdf(d2) / 100
        theta = (
            -S * exp_qt * n_prime_d1 * sigma / (2 * np.sqrt(T))
            - r * K * exp_rt * norm.cdf(d2)
            + q * S * exp_qt * norm.cdf(d1)
        ) / 365
    else:
        delta = exp_qt * (norm.cdf(d1) - 1)
        rho = -K * T * exp_rt * norm.cdf(-d2) / 100
        theta = (
            -S * exp_qt * n_prime_d1 * sigma / (2 * np.sqrt(T))
            + r * K * exp_rt * norm.cdf(-d2)
            - q * S * exp_qt * norm.cdf(-d1)
        ) / 365

    gamma = exp_qt * n_prime_d1 / (S * sigma * np.sqrt(T))
    vega = S * exp_qt * n_prime_d1 * np.sqrt(T) / 100

    return {
        "delta": round(delta, 6),
        "gamma": round(gamma, 6),
        "theta": round(theta, 6),
        "vega": round(vega, 6),
        "rho": round(rho, 6),
    }


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: Literal["call", "put"],
    q: float = 0.0,
    tol: float = 1e-6,
    max_iter: int = 200,
) -> float:
    """Solve implied volatility with Newton-Raphson.

    Args:
        market_price: Observed market price
        tol: Convergence tolerance
        max_iter: Maximum number of iterations

    Returns:
        Annualized implied volatility. Returns np.nan on failure.

    Raises:
        ValueError: If the market price is below intrinsic value
    """
    # Check intrinsic value first.
    intrinsic = max(0.0, S - K if option_type == "call" else K - S)
    if market_price < intrinsic - 1e-6:
        raise ValueError(f"Market price {market_price} is below intrinsic value {intrinsic}")

    # Brenner-Subrahmanyam initial approximation.
    sigma = np.sqrt(2 * np.pi / T) * market_price / S
    sigma = max(0.001, min(sigma, 5.0))

    for _ in range(max_iter):
        price = bs_price(S, K, T, r, sigma, option_type, q)
        vega = bs_greeks(S, K, T, r, sigma, option_type, q)["vega"] * 100  # restore per-1.0 unit

        diff = price - market_price
        if abs(diff) < tol:
            return round(sigma, 6)

        if abs(vega) < 1e-10:
            # Vega is near zero, fall back to bisection.
            try:
                return float(brentq(
                    lambda v: bs_price(S, K, T, r, v, option_type, q) - market_price,
                    1e-4, 10.0, xtol=tol, maxiter=200
                ))
            except ValueError:
                return np.nan

        sigma -= diff / vega
        sigma = max(1e-4, min(sigma, 10.0))  # clamp to a reasonable range

    return np.nan  # did not converge
```

### 4.2 Multi-Leg Portfolio Payoff Calculation

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class OptionLeg:
    """Single option leg definition.

    Attributes:
        option_type: "call" or "put"
        K: Strike price
        direction: +1 for Long / -1 for Short
        quantity: Number of contracts, defaults to 1
        premium: Actual traded premium, positive when paid and negative when received
        T: Time to expiration in years, used for theoretical Black-Scholes pricing
        sigma: Volatility used in pricing
    """
    option_type: Literal["call", "put"]
    K: float
    direction: int  # +1 or -1
    quantity: float = 1.0
    premium: float = 0.0
    T: float = 0.25
    sigma: float = 0.20


def compute_expiry_payoff(
    legs: list[OptionLeg],
    S_range: np.ndarray,
) -> np.ndarray:
    """Calculate the expiry payoff curve.

    Args:
        legs: Option legs
        S_range: Array of underlying prices

    Returns:
        Payoff array aligned with S_range, including premium cost
    """
    total_payoff = np.zeros(len(S_range))
    net_premium = sum(leg.direction * leg.quantity * leg.premium for leg in legs)

    for leg in legs:
        if leg.option_type == "call":
            intrinsic = np.maximum(S_range - leg.K, 0)
        else:
            intrinsic = np.maximum(leg.K - S_range, 0)
        total_payoff += leg.direction * leg.quantity * intrinsic

    return total_payoff - net_premium


def compute_theo_value(
    legs: list[OptionLeg],
    S_range: np.ndarray,
    r: float = 0.03,
    q: float = 0.0,
) -> np.ndarray:
    """Calculate the theoretical value curve under current Black-Scholes pricing.

    Args:
        legs: Option legs, each carrying T and sigma
        S_range: Array of underlying prices
        r: Risk-free rate
        q: Continuous dividend yield

    Returns:
        Theoretical PnL array
    """
    total_value = np.zeros(len(S_range))
    net_premium = sum(leg.direction * leg.quantity * leg.premium for leg in legs)

    for leg in legs:
        prices = np.array([
            bs_price(S, leg.K, leg.T, r, leg.sigma, leg.option_type, q)
            for S in S_range
        ])
        total_value += leg.direction * leg.quantity * prices

    return total_value - net_premium


def find_breakeven_points(
    S_range: np.ndarray,
    payoff: np.ndarray,
) -> list[float]:
    """Solve for break-even points numerically.

    Returns:
        A list of break-even points, from 0 to many depending on the structure
    """
    beps = []
    for i in range(len(S_range) - 1):
        if payoff[i] * payoff[i + 1] < 0:
            bep = brentq(
                lambda s: np.interp(s, S_range, payoff),
                S_range[i], S_range[i + 1],
                xtol=0.01
            )
            beps.append(round(bep, 2))
    return beps
```

### 4.3 Matplotlib Payoff Diagram

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def plot_payoff_diagram(
    legs: list[OptionLeg],
    S_current: float,
    r: float = 0.03,
    q: float = 0.0,
    title: str = "Option Payoff Diagram",
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """Plot the payoff diagram for an option portfolio.

    Args:
        legs: Option legs
        S_current: Current underlying price
        r: Risk-free rate
        q: Continuous dividend yield
        title: Chart title
        figsize: Figure size

    Returns:
        A matplotlib Figure object
    """
    K_values = [leg.K for leg in legs]
    S_lo = min(K_values) * 0.70
    S_hi = max(K_values) * 1.30
    S_range = np.linspace(S_lo, S_hi, 500)

    expiry_pnl = compute_expiry_payoff(legs, S_range)
    theo_pnl = compute_theo_value(legs, S_range, r, q)
    beps = find_breakeven_points(S_range, expiry_pnl)

    fig, ax = plt.subplots(figsize=figsize)

    # Shade profit and loss regions.
    ax.fill_between(S_range, expiry_pnl, 0,
                    where=(expiry_pnl >= 0), alpha=0.15, color="green", label="_nolegend_")
    ax.fill_between(S_range, expiry_pnl, 0,
                    where=(expiry_pnl < 0), alpha=0.15, color="red", label="_nolegend_")

    # Expiry payoff curve.
    ax.plot(S_range, expiry_pnl, color="steelblue", linewidth=2.0, label="Expiry P&L")

    # Theoretical value curve.
    ax.plot(S_range, theo_pnl, color="darkorange", linewidth=1.5,
            linestyle="--", label="Current theoretical value")

    # Zero axis.
    ax.axhline(0, color="black", linewidth=0.8, linestyle="-")

    # Current price line.
    ax.axvline(S_current, color="gray", linewidth=1.0, linestyle=":",
               label=f"Spot {S_current:.2f}")

    # Strike annotations.
    for K in K_values:
        ax.axvline(K, color="purple", linewidth=0.6, linestyle="--", alpha=0.5)
        ax.text(K, ax.get_ylim()[0], f"K={K}", fontsize=8,
                rotation=90, va="bottom", color="purple")

    # Break-even points.
    for bep in beps:
        ax.scatter([bep], [0], color="red", zorder=5, s=50)
        ax.annotate(f"BEP\n{bep:.2f}", xy=(bep, 0),
                    xytext=(bep, max(expiry_pnl) * 0.15),
                    fontsize=8, ha="center", color="red",
                    arrowprops=dict(arrowstyle="->", color="red", lw=0.8))

    # Max profit / max loss summary.
    max_p = max(expiry_pnl)
    max_l = min(expiry_pnl)
    stats_text = (
        f"Max profit: {'Unlimited' if max_p > 1e6 else f'{max_p:.2f}'}\n"
        f"Max loss: {'Unlimited' if max_l < -1e6 else f'{max_l:.2f}'}\n"
        f"Break-even: {', '.join([str(b) for b in beps]) if beps else 'None'}"
    )
    ax.text(0.02, 0.97, stats_text, transform=ax.transAxes,
            fontsize=9, va="top", bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    ax.set_xlabel("Underlying price")
    ax.set_ylabel("P&L")
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig
```

### 4.4 Plotly Interactive Payoff Diagram (Recommended for Frontend Display)

```python
import plotly.graph_objects as go

def plot_payoff_plotly(
    legs: list[OptionLeg],
    S_current: float,
    r: float = 0.03,
    q: float = 0.0,
    title: str = "Option Payoff Diagram",
    sigma_scenarios: list[float] | None = None,
) -> go.Figure:
    """Generate a Plotly interactive payoff diagram with optional multi-sigma scenarios.

    Args:
        sigma_scenarios: For example [0.10, 0.15, 0.20, 0.25, 0.30].
            If None, use each leg's own sigma.
    """
    K_values = [leg.K for leg in legs]
    S_range = np.linspace(min(K_values) * 0.70, max(K_values) * 1.30, 500)
    expiry_pnl = compute_expiry_payoff(legs, S_range)

    fig = go.Figure()

    # Expiry payoff.
    fig.add_trace(go.Scatter(
        x=S_range, y=expiry_pnl,
        name="Expiry P&L", line=dict(color="steelblue", width=2),
        fill="tozeroy",
        fillcolor="rgba(70,130,180,0.1)",
    ))

    # Theoretical value under multiple volatility scenarios.
    if sigma_scenarios:
        colors = ["#FF6B6B", "#FFA500", "#4CAF50", "#2196F3", "#9C27B0"]
        for i, sigma in enumerate(sigma_scenarios):
            scenario_legs = [
                OptionLeg(
                    option_type=leg.option_type, K=leg.K,
                    direction=leg.direction, quantity=leg.quantity,
                    premium=leg.premium, T=leg.T, sigma=sigma
                )
                for leg in legs
            ]
            theo = compute_theo_value(scenario_legs, S_range, r, q)
            fig.add_trace(go.Scatter(
                x=S_range, y=theo,
                name=f"IV={sigma*100:.0f}%",
                line=dict(color=colors[i % len(colors)], width=1.5, dash="dash"),
            ))
    else:
        theo_pnl = compute_theo_value(legs, S_range, r, q)
        fig.add_trace(go.Scatter(
            x=S_range, y=theo_pnl,
            name="Current theoretical value",
            line=dict(color="darkorange", width=1.5, dash="dash"),
        ))

    # Zero line and current price line.
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=0.8)
    fig.add_vline(x=S_current, line_dash="dot", line_color="gray",
                  annotation_text=f"Spot {S_current:.2f}", annotation_position="top right")

    # Strikes.
    for K in set(K_values):
        fig.add_vline(x=K, line_dash="dash", line_color="purple",
                      line_width=0.8, opacity=0.5)

    fig.update_layout(
        title=title,
        xaxis_title="Underlying price",
        yaxis_title="P&L",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
```

### 4.5 Greeks Profile vs Underlying Price

```python
def plot_greeks_profile(
    legs: list[OptionLeg],
    S_current: float,
    r: float = 0.03,
    q: float = 0.0,
    greeks_to_plot: list[str] | None = None,
) -> go.Figure:
    """Plot portfolio Greeks as functions of the underlying price.

    Args:
        greeks_to_plot: Defaults to ["delta", "gamma", "vega", "theta"]
    """
    if greeks_to_plot is None:
        greeks_to_plot = ["delta", "gamma", "vega", "theta"]

    K_values = [leg.K for leg in legs]
    S_range = np.linspace(min(K_values) * 0.70, max(K_values) * 1.30, 300)

    # Compute portfolio Greeks.
    greek_values = {g: np.zeros(len(S_range)) for g in greeks_to_plot}
    for leg in legs:
        for j, S in enumerate(S_range):
            g = bs_greeks(S, leg.K, leg.T, r, leg.sigma, leg.option_type, q)
            for name in greeks_to_plot:
                greek_values[name][j] += leg.direction * leg.quantity * g[name]

    # Plot subplots.
    from plotly.subplots import make_subplots
    n = len(greeks_to_plot)
    fig = make_subplots(rows=n, cols=1, shared_xaxes=True,
                        subplot_titles=[g.capitalize() for g in greeks_to_plot])

    greek_colors = {"delta": "steelblue", "gamma": "green",
                    "theta": "red", "vega": "darkorange", "rho": "purple"}

    for i, name in enumerate(greeks_to_plot, start=1):
        fig.add_trace(
            go.Scatter(x=S_range, y=greek_values[name],
                       name=name.capitalize(),
                       line=dict(color=greek_colors.get(name, "gray"), width=2)),
            row=i, col=1
        )
        fig.add_hline(y=0, line_dash="dot", line_color="black",
                      line_width=0.5, row=i, col=1)
        fig.add_vline(x=S_current, line_dash="dash", line_color="gray",
                      line_width=0.8, row=i, col=1)

    fig.update_layout(
        title="Greeks Profile",
        height=200 * n,
        showlegend=False,
        template="plotly_white",
    )

    return fig
```

---

## 5. Practical Usage

### 5.1 Strategy Selection Decision Tree by Market View

```
Market view
├── Strongly bullish
│   ├── Willing to pay premium → Long Call
│   └── Want lower cost → Bull Call Spread
├── Moderately bullish
│   ├── Already hold the underlying → Covered Call (income enhancement)
│   └── No existing position → Bull Put Spread (net credit)
├── Moderately bearish
│   ├── Already hold the underlying → Protective Put or Collar
│   └── No existing position → Bear Call Spread (net credit)
├── Strongly bearish
│   ├── Willing to pay premium → Long Put
│   └── Want lower cost → Bear Put Spread
├── Range-bound market (low-IV environment)
│   ├── Wide range → Short Strangle
│   ├── Narrow range → Short Straddle
│   └── Want limited risk → Iron Condor / Iron Butterfly
└── Large move expected (low-IV environment)
    ├── Direction unclear → Long Straddle / Long Strangle
    └── Slight directional bias → Call / Put Back Spread
```

### 5.2 Volatility Environment → Strategy Mapping

| IV Regime | Rule of Thumb | Suitable Strategies | Strategies to Avoid |
|---------|----------|----------|----------|
| Low IV (< 20th percentile) | IV Rank < 20 | Long Straddle, Long Strangle, Back Spread | Short strategies, because premium is too thin |
| Normal IV (20th to 80th percentile) | IV Rank 20 to 80 | Vertical spreads, Calendar Spread, Diagonal | Single-leg positions with asymmetric risk |
| High IV (> 80th percentile) | IV Rank > 80 | Short Straddle, Iron Condor, Covered Call | Long single-leg options due to rich premium |

**IV Rank formula**:
```python
iv_rank = (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) * 100
```

**IV Percentile**: The historical percentile rank of current IV over the last 252 trading days.

### 5.3 When to Roll or Adjust

#### Rolling
- **Trigger**: Option Delta moves outside the target range, or time to expiration < 21 days
- **Rolling Up / Down**: Close the current leg and reopen at a higher / lower strike while keeping the same directional bias
- **Rolling Out**: Close the near-month leg and reopen further out on the curve to harvest additional time value
- **Cost assessment**: Compare the net debit / credit of the roll with the payoff from simply holding to expiration

#### Adjusting
- **Delta-neutral rebalancing**: Hedge with underlying or options when portfolio Delta deviates from target by more than ±0.10
- **Gamma scalping**: Under a Long Gamma portfolio, hedge Delta after large underlying moves to lock in gains
- **Stop-loss rule**: Force liquidation when losses reach 2× the initial premium received, a common rule for Iron Condors

#### Common Adjustment Examples

**Iron Condor gets breached**:
```
Underlying rallies above the short call:
1. Close the call spread and realize the loss
2. Reassess directional view:
   - Still bullish → reopen a higher put spread to preserve neutrality
   - Not bullish → close the entire portfolio
```

**Covered Call faces assignment risk**:
```
Underlying approaches the call strike:
1. Assess whether you are willing to sell the underlying at that price
   - Yes → allow assignment and keep premium + capital gain
   - No → Roll Up & Out to a higher strike and/or later expiration
```

---

## Quick Usage Example

```python
# Example: Iron Condor payoff diagram
legs = [
    OptionLeg("put",  K=90,  direction=-1, premium=1.5, T=0.083, sigma=0.20),
    OptionLeg("put",  K=85,  direction=+1, premium=0.5, T=0.083, sigma=0.20),
    OptionLeg("call", K=110, direction=-1, premium=1.5, T=0.083, sigma=0.20),
    OptionLeg("call", K=115, direction=+1, premium=0.5, T=0.083, sigma=0.20),
]

fig = plot_payoff_plotly(
    legs, S_current=100.0,
    title="Iron Condor (85/90/110/115, 1 month)",
    sigma_scenarios=[0.15, 0.20, 0.25, 0.30],
)
fig.show()

# Implied volatility example
iv = implied_volatility(
    market_price=5.0, S=100, K=100,
    T=0.25, r=0.03, option_type="call"
)
print(f"Implied volatility: {iv:.2%}")  # about 0.20
```
