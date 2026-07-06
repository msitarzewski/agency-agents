---
name: correlation-analysis
description: Correlation and cointegration analysis — co-movement discovery, deep return-correlation analysis, sector clustering, realized correlation, Engle-Granger / Johansen cointegration, half-life, Kalman dynamic hedge ratio, cross-market linkage analysis, and pair-trading signal generation
category: analysis
---

# Correlation and Cointegration Analysis

## Overview

Correlation analysis is a foundational tool for pairs trading, portfolio construction, and risk management. This skill covers four analysis modes (co-movement discovery / return-correlation deep dive / sector clustering / realized correlation), a full cointegration-testing framework, cross-market linkage analysis, and the complete workflow from analytics to pair-trading signals.

---

## Mode 1: Co-Movement Discovery

**Use case**: Given a target asset, scan a universe for highly correlated assets and build a candidate pool with similar industry or factor exposure, for use in pairs trading or substitute identification.

### Workflow

```
1. Pull daily return series for the target asset and N candidates
2. Compute Pearson / Spearman correlations between the target and each candidate
3. Rank by correlation in descending order and keep Top-K (usually K=10-20)
4. Run cointegration tests on the Top-K set to retain pairs with real long-run equilibrium
5. Output the candidate pool and a correlation summary
```

```python
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

def scan_correlated_assets(
    target_returns: pd.Series,
    universe_returns: pd.DataFrame,
    top_k: int = 20,
    min_corr: float = 0.5,
    method: str = "pearson",
) -> pd.DataFrame:
    """Scan for assets that are highly correlated with the target asset.

    Args:
        target_returns: Daily return series for the target asset
        universe_returns: Candidate-universe return matrix, columns are symbols
        top_k: Number of top candidates to return
        min_corr: Minimum absolute-correlation threshold
        method: "pearson" or "spearman"

    Returns:
        A DataFrame containing symbol / corr / p_value / rank
    """
    aligned = universe_returns.dropna(axis=1, how="any")
    aligned, target_aligned = aligned.align(target_returns, join="inner", axis=0)

    results = []
    for col in aligned.columns:
        if method == "spearman":
            corr, p = spearmanr(target_aligned, aligned[col])
        else:
            corr, p = pearsonr(target_aligned, aligned[col])
        results.append({"symbol": col, "corr": corr, "p_value": p})

    df = pd.DataFrame(results)
    df = df[df["corr"].abs() >= min_corr].sort_values("corr", ascending=False)
    df["rank"] = range(1, len(df) + 1)
    return df.head(top_k).reset_index(drop=True)
```

**Screening guidance**:

| Correlation | Conclusion | Follow-up Action |
|---------|------|---------|
| > 0.8 | Strong same-direction co-movement | Send to the cointegration test queue |
| 0.6 - 0.8 | Moderate co-movement | Check industry / factor alignment before cointegration |
| < 0.6 | Weak correlation | Usually unsuitable for pairs trading |
| Negative and < -0.6 | Strong inverse co-movement | Can be used in hedged portfolios, but be careful with spread direction |

---

## Mode 2: Deep Return-Correlation Analysis

**Use case**: Run a full bivariate correlation study on two assets, including multiple correlation coefficients, Beta / R², rolling correlation, and spread Z-Score.

### Core Metrics

```python
import statsmodels.api as sm
from scipy.stats import pearsonr, spearmanr, kendalltau

def bivariate_correlation_analysis(
    y: pd.Series,
    x: pd.Series,
    rolling_window: int = 60,
) -> dict:
    """Run deep correlation analysis for two assets.

    Args:
        y: Daily return series of asset A
        x: Daily return series of asset B
        rolling_window: Rolling-window length in trading days

    Returns:
        Dict of correlation statistics
    """
    # Align the two series.
    df = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    y_clean, x_clean = df["y"], df["x"]

    # Static correlations.
    pearson_r, pearson_p = pearsonr(y_clean, x_clean)
    spearman_r, spearman_p = spearmanr(y_clean, x_clean)
    kendall_r, kendall_p = kendalltau(y_clean, x_clean)

    # OLS: y = α + β·x
    x_const = sm.add_constant(x_clean)
    ols = sm.OLS(y_clean, x_const).fit()
    beta = ols.params["x"]
    alpha = ols.params["const"]
    r_squared = ols.rsquared

    # Rolling Pearson correlation.
    rolling_corr = y_clean.rolling(rolling_window).corr(x_clean)

    # Spread and Z-Score using the hedge ratio.
    spread = y_clean - beta * x_clean
    spread_mean = spread.rolling(rolling_window).mean()
    spread_std = spread.rolling(rolling_window).std()
    z_score = (spread - spread_mean) / spread_std

    return {
        "pearson": {"r": round(pearson_r, 4), "p": round(pearson_p, 6)},
        "spearman": {"r": round(spearman_r, 4), "p": round(spearman_p, 6)},
        "kendall": {"r": round(kendall_r, 4), "p": round(kendall_p, 6)},
        "beta": round(beta, 4),
        "alpha": round(alpha, 6),
        "r_squared": round(r_squared, 4),
        "rolling_corr": rolling_corr,
        "spread": spread,
        "z_score": z_score,
        "spread_mean": spread_mean,
        "spread_std": spread_std,
    }
```

### Correlation-Coefficient Selection Guide

| Coefficient | Assumption | Best Use Case | Not Suitable When |
|------|------|---------|--------|
| Pearson | Linear, approximately normal | Return series | Heavy tails / many outliers |
| Spearman | Monotonic relationship | Ranking / quantile analysis, many outliers | When magnitude information matters |
| Kendall | Order consistency | Small samples, unknown distribution | Large samples due to slower computation |

**Practical rule in finance**: Usually report all three coefficients. If Pearson and Spearman differ by more than 0.1, the relationship is likely nonlinear or heavy-tailed, and Spearman should carry more weight.

---

## Mode 3: Sector Clustering

**Use case**: Run hierarchical clustering on the correlation matrix of N assets to discover sector structure, check portfolio diversification, and identify similar assets.

```python
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
import seaborn as sns

def sector_clustering(
    returns: pd.DataFrame,
    method: str = "ward",
    n_clusters: int = 5,
    figsize: tuple = (12, 10),
) -> dict:
    """Run sector clustering analysis.

    Args:
        returns: Multi-asset daily return matrix, columns are symbols
        method: Linkage method: "ward" / "complete" / "average"
        n_clusters: Target number of clusters
        figsize: Heatmap size

    Returns:
        Dict containing the correlation matrix, cluster labels, and figure objects
    """
    # 1. Correlation matrix
    corr_matrix = returns.corr(method="pearson")

    # 2. Distance matrix where distance = 1 - |correlation|
    distance_matrix = 1 - corr_matrix.abs()
    condensed = squareform(distance_matrix.values, checks=False)

    # 3. Hierarchical clustering
    linkage_matrix = linkage(condensed, method=method)
    labels = fcluster(linkage_matrix, n_clusters, criterion="maxclust")
    cluster_df = pd.DataFrame({"symbol": corr_matrix.columns, "cluster": labels})

    # 4. Heatmap sorted by cluster
    order = cluster_df.sort_values("cluster").index
    sorted_corr = corr_matrix.iloc[order, order]

    fig_heatmap, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        sorted_corr,
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        annot=len(corr_matrix) <= 20,
        fmt=".2f",
        ax=ax,
        cbar_kws={"label": "Pearson correlation"},
    )
    ax.set_title(f"Correlation Heatmap ({method.upper()} clustering order)")

    # 5. Dendrogram
    fig_dendro, ax2 = plt.subplots(figsize=(figsize[0], 6))
    dendrogram(
        linkage_matrix,
        labels=list(corr_matrix.columns),
        ax=ax2,
        leaf_rotation=90,
        color_threshold=0,
    )
    ax2.set_title(f"Hierarchical Dendrogram ({method.upper()} linkage)")
    ax2.set_ylabel("Distance")

    return {
        "corr_matrix": corr_matrix,
        "cluster_labels": cluster_df,
        "linkage_matrix": linkage_matrix,
        "fig_heatmap": fig_heatmap,
        "fig_dendrogram": fig_dendro,
        "n_clusters": n_clusters,
    }
```

### Comparison of Three Linkage Methods

| Method | Feature | Best Use Case | Weakness |
|------|------|---------|------|
| Ward | Minimizes within-cluster variance, gives compact clusters | **Default recommendation**, stock-sector discovery | Works best for spherical clusters, weaker for irregular shapes |
| Complete | Uses maximum pairwise distance, conservative | When high within-cluster similarity is required | Can produce elongated clusters |
| Average | Uses average distance, compromise approach | General analysis where compactness is not the top priority | Sensitive to noise |

---

## Mode 4: Realized Correlation

> **Authoritative Source**: This section is the single source of truth for regime classification rules.
> Other files (e.g., `agent/src/agent/context.py` Layer 3, `docs/trade-attribution-design.md`) reference this definition.

**Use case**: Compute rolling correlation time series and analyze conditional correlation by market regime (bull / bear / high-volatility) to discover how correlation evolves dynamically.

```python
def realized_correlation(
    y: pd.Series,
    x: pd.Series,
    benchmark: pd.Series,
    windows: list = [20, 60, 120],
    vol_window: int = 20,
    vol_threshold: float = 1.5,
) -> dict:
    """Rolling realized correlation plus regime-conditional correlation.

    Args:
        y, x: Daily return series of two assets
        benchmark: Daily return series of the benchmark index used for regime labeling
        windows: List of rolling windows in trading days
        vol_window: Volatility window
        vol_threshold: High-vol threshold as a multiple of average vol

    Returns:
        Rolling correlation series and conditional-correlation summary
    """
    df = pd.concat([y.rename("y"), x.rename("x"),
                    benchmark.rename("bm")], axis=1).dropna()

    # Rolling correlation time series.
    rolling_corrs = {}
    for w in windows:
        rolling_corrs[f"roll_{w}d"] = df["y"].rolling(w).corr(df["x"])

    # Regime labels.
    # N-day rolling mean (N = 252 for US equity; use 244 for A-share, 365 for crypto)
    bm_ret_252 = df["bm"].rolling(252).mean()
    bm_vol = df["bm"].rolling(vol_window).std()
    # N-day rolling mean of volatility (N = 252 for US equity; use 244 for A-share, 365 for crypto)
    bm_vol_mean = bm_vol.rolling(252).mean()

    df["regime"] = "sideways"
    df.loc[df["bm"] > bm_ret_252, "regime"] = "bull"
    df.loc[df["bm"] < -bm_ret_252.abs(), "regime"] = "bear"
    df.loc[bm_vol > bm_vol_mean * vol_threshold, "regime"] = "high_vol"

    # Conditional correlation.
    cond_corr = {}
    for regime in ["bull", "bear", "sideways", "high_vol"]:
        mask = df["regime"] == regime
        if mask.sum() >= 30:
            r, p = pearsonr(df.loc[mask, "y"], df.loc[mask, "x"])
            cond_corr[regime] = {"corr": round(r, 4), "p": round(p, 6), "n": int(mask.sum())}
        else:
            cond_corr[regime] = {"corr": None, "p": None, "n": int(mask.sum())}

    return {
        "rolling_corrs": pd.DataFrame(rolling_corrs),
        "regime_labels": df["regime"],
        "conditional_corr": cond_corr,
    }
```

**Market-Adaptive Window (N)**:
The rolling window for regime classification adapts to market type:
- US equity: N = 252 (standard trading days per year)
- A-share (China): N = 244 (fewer trading days due to holidays)
- Crypto: N = 365 (24/7 market)

The default value 252 in the function signature targets US equity.
Callers for other markets should adjust the rolling windows accordingly.

**Fallback for Short Data**:
If available data length is shorter than N days (the market-equivalent annual window),
regime classification falls back to fixed-threshold definitions:
- Bull: cumulative benchmark return over the available period > +10%
- Bear: cumulative benchmark return over the available period < -10%
- High-vol / Sideways: not applicable in fallback mode

### Typical Correlation Behavior by Market Regime

| Market Regime | Equity-Equity Correlation | Equity-Bond Correlation | A-Share Characteristic |
|---------|---------|---------|--------|
| Bull | Medium (0.4-0.6) | Low or negative | Small-cap names tend to move together strongly |
| Bear | **High (0.7-0.9)** | Negative (safe-haven effect) | Broad selloff, correlation jumps sharply |
| High volatility | **Very high (0.8+)** | Negative | In crises, correlation often converges toward 1 |
| Sideways | Low (0.2-0.4) | Near zero | Stock dispersion rises, ideal for pairs trading |

---

## Cointegration Analysis

Correlation measures the degree of co-movement. Cointegration measures whether a **long-run equilibrium relationship** exists. High correlation does not guarantee cointegration, and low correlation does not rule it out.

### Engle-Granger Two-Step Method

Suitable for two-variable pairs, quick and intuitive.

```python
from statsmodels.tsa.stattools import coint, adfuller
import statsmodels.api as sm
import numpy as np

def engle_granger_coint(
    y: pd.Series,
    x: pd.Series,
    significance: float = 0.05,
) -> dict:
    """Run the Engle-Granger two-step cointegration test.

    H0: No cointegration relationship exists (residuals contain a unit root).

    Args:
        y, x: Two price series. These must be non-stationary series,
            usually prices rather than returns.
        significance: Significance level

    Returns:
        Test results and spread series
    """
    # Step 1: estimate the cointegrating vector with OLS.
    x_const = sm.add_constant(x)
    ols = sm.OLS(y, x_const).fit()
    hedge_ratio = ols.params[x.name if x.name else "x"]
    intercept = ols.params["const"]
    residuals = ols.resid

    # Step 2: test residual stationarity with ADF.
    adf_res = adfuller(residuals, autolag="AIC")
    adf_stat, adf_p = adf_res[0], adf_res[1]

    # statsmodels coint wrapper.
    coint_stat, coint_p, crit_vals = coint(y, x)

    return {
        "method": "Engle-Granger",
        "is_cointegrated": coint_p < significance,
        "coint_p": round(coint_p, 6),
        "coint_stat": round(coint_stat, 4),
        "critical_values": {"1%": crit_vals[0], "5%": crit_vals[1], "10%": crit_vals[2]},
        "hedge_ratio": round(hedge_ratio, 6),
        "intercept": round(intercept, 6),
        "spread": residuals,
        "adf_on_spread": {"stat": round(adf_stat, 4), "p": round(adf_p, 6)},
    }
```

**Note**: Engle-Granger can detect only one cointegrating vector, and the test result depends on the ordering of `y` and `x`. In practice, test both directions and keep the direction with the smaller p-value.

### Johansen Cointegration Test for Multiple Variables

Suitable for three or more assets and for estimating the number of cointegrating vectors (rank).

```python
from statsmodels.tsa.vector_ar.vecm import coint_johansen

def johansen_coint(
    prices: pd.DataFrame,
    det_order: int = 0,
    k_ar_diff: int = 1,
) -> dict:
    """Run the Johansen cointegration test.

    Args:
        prices: Multi-asset price matrix, columns are symbols.
            The series must be non-stationary.
        det_order: Deterministic term. -1=no intercept, 0=intercept, 1=trend
        k_ar_diff: Number of lagged differences in the VAR, usually 1-5 chosen by AIC

    Returns:
        Trace-test and max-eigenvalue-test results
    """
    result = coint_johansen(prices.dropna(), det_order=det_order, k_ar_diff=k_ar_diff)
    n = prices.shape[1]

    # Trace test.
    trace_results = []
    for i in range(n):
        trace_results.append({
            "H0_rank_leq": i,
            "trace_stat": round(result.lr1[i], 4),
            "crit_10pct": result.cvt[i, 0],
            "crit_5pct": result.cvt[i, 1],
            "crit_1pct": result.cvt[i, 2],
            "reject_5pct": result.lr1[i] > result.cvt[i, 1],
        })

    # Max-eigenvalue test.
    maxeig_results = []
    for i in range(n):
        maxeig_results.append({
            "H0_rank_eq": i,
            "maxeig_stat": round(result.lr2[i], 4),
            "crit_10pct": result.cvm[i, 0],
            "crit_5pct": result.cvm[i, 1],
            "crit_1pct": result.cvm[i, 2],
            "reject_5pct": result.lr2[i] > result.cvm[i, 1],
        })

    # Cointegrating vectors, normalized.
    coint_vectors = pd.DataFrame(
        result.evec[:, :sum(r["reject_5pct"] for r in trace_results)],
        index=prices.columns,
    )

    return {
        "method": "Johansen",
        "n_coint_vectors_trace": sum(r["reject_5pct"] for r in trace_results),
        "trace_test": pd.DataFrame(trace_results),
        "maxeig_test": pd.DataFrame(maxeig_results),
        "coint_vectors": coint_vectors,
        "eigenvalues": result.eig,
    }
```

**Johansen rank interpretation rules**:

```
Start the trace test from H0: rank=0 and move upward.
The first rank that cannot be rejected is the estimated cointegration rank.

rank = 0   → no cointegration
rank = 1   → one cointegrating vector (most common, long-run equilibrium for a pair)
rank = k-1 → k-1 cointegrating vectors (system is tightly linked)
rank = k   → the series themselves are stationary, so cointegration is not needed
```

### Half-Life Calculation

Half-life measures how long a spread takes to mean-revert after deviating from equilibrium. It is a practical reference for expected holding period in pairs trading.

```python
def compute_half_life(spread: pd.Series) -> float:
    """Estimate mean-reversion half-life with OLS, in days.

    Principle:
        Estimate ΔSpread_t = λ·Spread_{t-1} + ε
        Half-life = -ln(2) / λ, where λ must be negative for mean reversion

    Args:
        spread: Spread series, which should be stationary

    Returns:
        Half-life in trading days. Negative or infinite values imply divergence.
    """
    spread_lag = spread.shift(1)
    delta = spread.diff()
    df = pd.concat([delta, spread_lag], axis=1).dropna()
    df.columns = ["delta", "lag"]

    x_const = sm.add_constant(df["lag"])
    ols = sm.OLS(df["delta"], x_const).fit()
    lam = ols.params["lag"]

    if lam >= 0:
        return float("inf")  # no mean reversion

    half_life = -np.log(2) / lam
    return round(half_life, 1)
```

**Half-life reference ranges**:

| Half-Life | Meaning | Trading Guidance |
|-------|------|---------|
| < 5 days | Extremely fast reversion | Intraday or overnight trading, friction cost matters |
| 5-20 days | Fast reversion | Ideal range for short-term pairs trading |
| 20-60 days | Medium-speed reversion | Medium-term holding, rolling windows 60-120 days |
| 60-180 days | Slow reversion | Long holding period, monitor cointegration stability |
| > 180 days | Near random walk | High pairs-trading risk, use cautiously |

### Kalman Filter Dynamic Hedge Ratio

Static OLS hedge ratios cannot capture gradual drift in the cointegration relationship. A Kalman filter provides a continuously updated dynamic hedge ratio.

```python
import numpy as np

def kalman_hedge_ratio(
    y: pd.Series,
    x: pd.Series,
    delta: float = 1e-4,
    vt: float = 1.0,
) -> pd.DataFrame:
    """Estimate a dynamic hedge ratio with a Kalman filter.

    State equation:
        β_t = β_{t-1} + w_t,  w ~ N(0, Q)
    Observation equation:
        y_t = β_t · x_t + v_t,  v ~ N(0, R)

    Args:
        y: Price series of asset A
        x: Price series of asset B
        delta: State-noise intensity. Larger means faster hedge-ratio adaptation
        vt: Observation-noise variance

    Returns:
        DataFrame containing the dynamic hedge ratio and spread
    """
    n = len(y)
    # State: [β, α] = hedge ratio + intercept
    Wt = delta / (1 - delta) * np.eye(2)
    Vt = vt

    # Initialization
    theta = np.zeros((n, 2))
    P = np.zeros((n, 2, 2))
    P[0] = np.eye(2)

    spread = np.zeros(n)
    spread[0] = float("nan")

    for t in range(1, n):
        F = np.array([x.iloc[t], 1.0])

        # Predict
        theta_pred = theta[t - 1]
        P_pred = P[t - 1] + Wt

        # Innovation
        innovation = y.iloc[t] - F @ theta_pred
        S = F @ P_pred @ F.T + Vt

        # Kalman gain
        K = P_pred @ F.T / S

        # Update
        theta[t] = theta_pred + K * innovation
        P[t] = (np.eye(2) - np.outer(K, F)) @ P_pred

        spread[t] = y.iloc[t] - theta[t, 0] * x.iloc[t] - theta[t, 1]

    return pd.DataFrame({
        "hedge_ratio": theta[:, 0],
        "intercept": theta[:, 1],
        "spread": spread,
    }, index=y.index)
```

**Static vs dynamic hedge-ratio comparison**:

| Method | Strength | Weakness | Best Use Case |
|------|------|------|------|
| OLS | Simple, stable | Cannot capture time variation | Short-term stable pairs |
| Rolling OLS | Time-varying, intuitive | Window-sensitive, endpoint effect | Medium-term pairs |
| Kalman Filter | Real-time, continuous update | `delta` is harder to tune | Long-term or structurally shifting pairs |

---

## Cross-Market Correlation

### Correlation Across China A-Share Sectors

```python
# Typical China A-share sector-correlation patterns
ASHARE_SECTOR_PATTERNS = {
    "strong_pairs_gt_0_7": [
        "Banks & insurance",
        "Baijiu & consumer staples",
        "New energy & solar",
        "Defense & aerospace",
    ],
    "medium_pairs_0_4_to_0_7": [
        "Pharma & consumer",
        "Technology & semiconductors",
        "Real estate & building materials",
    ],
    "low_or_negative_lt_0_3": [
        "Gold & technology",
        "Utilities & cyclicals",
        "Consumer & cyclicals",
    ],
}
```

### Cross-Market Linkage Analysis

```python
def cross_market_correlation(
    markets: dict,  # {"China A-shares": series, "Hong Kong": series, "crypto": series, "US": series}
    rolling_window: int = 60,
    lag_days: list = [0, 1, 2, 3],
) -> dict:
    """Cross-market correlation plus lead-lag analysis.

    Args:
        markets: Daily return series for each market
        rolling_window: Rolling window
        lag_days: List of lags to test

    Returns:
        Correlation matrix, lead-lag analysis, and rolling correlation
    """
    df = pd.DataFrame(markets).dropna()

    # Static correlation matrix
    static_corr = df.corr()

    # Lead-lag correlation to detect cross-market transmission
    lead_lag = {}
    mkt_names = list(markets.keys())
    for i, m1 in enumerate(mkt_names):
        for m2 in mkt_names[i + 1:]:
            pair_key = f"{m1}_{m2}"
            lead_lag[pair_key] = {}
            for lag in lag_days:
                if lag == 0:
                    r, _ = pearsonr(df[m1], df[m2])
                else:
                    r, _ = pearsonr(df[m1].iloc[lag:], df[m2].iloc[:-lag])
                lead_lag[pair_key][f"lag_{lag}d"] = round(r, 4)

    # Rolling correlation
    rolling_corrs = {}
    for i, m1 in enumerate(mkt_names):
        for m2 in mkt_names[i + 1:]:
            key = f"{m1}_{m2}"
            rolling_corrs[key] = df[m1].rolling(rolling_window).corr(df[m2])

    return {
        "static_corr": static_corr,
        "lead_lag": pd.DataFrame(lead_lag).T,
        "rolling_corrs": pd.DataFrame(rolling_corrs),
    }
```

### Empirical Cross-Market Linkage Patterns

| Market Pair | Average Correlation | Transmission Direction | Lag |
|-------|---------|---------|------|
| China A-shares ↔ Hong Kong | 0.5-0.7 | Two-way, Hong Kong slightly leads | 0-1 day |
| China A-shares ↔ U.S. equities | 0.2-0.4 | U.S. leads overnight | 1 day |
| BTC ↔ ETH | 0.7-0.9 | Highly synchronous | < 1 hour |
| China A-shares ↔ BTC | 0.0-0.2 | Mostly independent, except correlation spikes in crises | Unstable |
| U.S. equities ↔ BTC | 0.1-0.4 | U.S. leads through institutional capital flows | Within 1 day |
| RMB exchange rate ↔ China A-shares | -0.2 - 0.3 | RMB weakness → foreign outflows → China A-share weakness | 0-2 days |

### Impact of FX Factors on Cross-Market Correlation

Cross-market correlation analysis must distinguish between local-currency returns and FX-adjusted returns. Otherwise, exchange-rate moves can create spurious correlation or hide the true one.

```python
def fx_adjusted_correlation(
    foreign_price: pd.Series,   # foreign-market price, denominated in foreign currency
    domestic_price: pd.Series,  # domestic-market price
    fx_rate: pd.Series,         # foreign currency / domestic currency, e.g. USD/CNY
) -> dict:
    """Cross-market correlation adjusted for FX effects.

    Args:
        foreign_price: Foreign-market price series in foreign currency
        domestic_price: Domestic-market price series in domestic currency
        fx_rate: FX series expressed as foreign / domestic

    Returns:
        Raw correlation vs FX-adjusted correlation
    """
    # Domestic-currency foreign return = foreign return + FX return
    foreign_ret = foreign_price.pct_change()
    fx_ret = fx_rate.pct_change()
    foreign_ret_cny = (1 + foreign_ret) * (1 + fx_ret) - 1

    domestic_ret = domestic_price.pct_change()

    df = pd.concat([foreign_ret.rename("foreign_raw"),
                    foreign_ret_cny.rename("foreign_domestic"),
                    domestic_ret.rename("domestic"),
                    fx_ret.rename("fx")], axis=1).dropna()

    raw_corr, _ = pearsonr(df["foreign_raw"], df["domestic"])
    adj_corr, _ = pearsonr(df["foreign_domestic"], df["domestic"])
    fx_corr, _ = pearsonr(df["fx"], df["domestic"])

    return {
        "raw_corr_foreign_domestic": round(raw_corr, 4),
        "fx_adjusted_corr": round(adj_corr, 4),
        "fx_domestic_corr": round(fx_corr, 4),
        "fx_contribution": round(adj_corr - raw_corr, 4),
        "note": "fx_contribution > 0 means FX amplified cross-market correlation",
    }
```

### Correlation Breakdown During Crises

During crises, equity correlation converges toward 1 and diversification breaks down. This is one of the central challenges in portfolio risk management.

```python
def correlation_breakdown_test(
    returns: pd.DataFrame,
    crisis_threshold: float = -0.02,  # one-day benchmark drop threshold for crisis days
    benchmark_col: str = None,
    window: int = 20,
) -> dict:
    """Detect jumps in correlation during crisis periods.

    Args:
        returns: Multi-asset daily return matrix
        crisis_threshold: Benchmark return below this level defines a crisis day
        benchmark_col: Benchmark column name. If None, use cross-sectional mean return
        window: Window for rolling average correlation

    Returns:
        Comparison of correlation in normal periods vs crisis periods
    """
    if benchmark_col:
        bm = returns[benchmark_col]
    else:
        bm = returns.mean(axis=1)

    crisis_mask = bm < crisis_threshold
    normal_mask = ~crisis_mask

    # Average pairwise correlation for each period
    def avg_corr(df_subset: pd.DataFrame) -> float:
        if len(df_subset) < 5:
            return float("nan")
        c = df_subset.corr()
        upper = c.where(np.triu(np.ones(c.shape), k=1).astype(bool))
        return float(upper.stack().mean())

    crisis_corr = avg_corr(returns[crisis_mask])
    normal_corr = avg_corr(returns[normal_mask])

    # Rolling average correlation to detect structural change
    rolling_avg_corr = pd.Series(dtype=float, index=returns.index)
    for i in range(window, len(returns)):
        sub = returns.iloc[i - window:i]
        rolling_avg_corr.iloc[i] = avg_corr(sub)

    return {
        "normal_avg_corr": round(normal_corr, 4),
        "crisis_avg_corr": round(crisis_corr, 4),
        "corr_jump": round(crisis_corr - normal_corr, 4),
        "crisis_days": int(crisis_mask.sum()),
        "normal_days": int(normal_mask.sum()),
        "rolling_avg_corr": rolling_avg_corr,
    }
```

---

## Pair-Trading Signal Generation

### Full Workflow From Correlation to Signal

```
Step 1: Asset screening
  - Run scan_correlated_assets and keep candidate pairs with Pearson > 0.6
  - Run engle_granger_coint and keep pairs with p < 0.05

Step 2: Spread quality assessment
  - Run compute_half_life and keep pairs with half-life between 5 and 60 days
  - Test spread stationarity with ADF and require p < 0.05
  - Measure how often the absolute Z-Score exceeds 1.5 over the last 12 months
    to estimate trading frequency

Step 3: Hedge-ratio selection
  - Use static OLS for stable pairs
  - Use Kalman Filter for long-lived or drifting pairs

Step 4: Signal generation
  - Compute rolling Z-Score with a lookback of 2-3× half-life
  - Generate long / short / exit signals based on thresholds

Step 5: Signal monitoring
  - Recompute Z-Score daily
  - Re-run cointegration monthly to avoid broken relationships
  - Warn if half-life exceeds 2× the original value
```

### Z-Score Signal Generation

```python
def generate_pair_signals(
    y_price: pd.Series,
    x_price: pd.Series,
    lookback: int = 60,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float = 3.5,
    use_kalman: bool = False,
) -> pd.DataFrame:
    """Generate pair-trading signals.

    Args:
        y_price, x_price: Two price series
        lookback: Rolling Z-Score lookback, usually 2-3× half-life
        entry_z: Entry threshold
        exit_z: Exit threshold, usually near mean reversion
        stop_z: Stop threshold. Crossing it suggests cointegration may have broken
        use_kalman: Whether to use a Kalman dynamic hedge ratio

    Returns:
        DataFrame containing signals, Z-Score, and positions
    """
    if use_kalman:
        kf = kalman_hedge_ratio(y_price, x_price)
        spread = kf["spread"]
    else:
        y_ret = y_price.pct_change()
        x_ret = x_price.pct_change()
        res = bivariate_correlation_analysis(y_ret, x_ret, lookback)
        hedge_ratio = abs(res["beta"])
        spread = np.log(y_price) - hedge_ratio * np.log(x_price)

    spread_mean = spread.rolling(lookback).mean()
    spread_std = spread.rolling(lookback).std()
    z_score = (spread - spread_mean) / spread_std

    # Signal state machine to avoid repeated re-entry.
    signal_y = pd.Series(0.0, index=y_price.index)
    signal_x = pd.Series(0.0, index=x_price.index)
    position = 0  # 0=flat, 1=long spread, -1=short spread

    for i in range(lookback, len(z_score)):
        z = z_score.iloc[i]
        if np.isnan(z):
            continue

        if position == 0:
            if z < -entry_z:
                position = 1   # spread is too low: buy y, sell x
            elif z > entry_z:
                position = -1  # spread is too high: sell y, buy x
        elif position == 1:
            if z > -exit_z or z > stop_z:
                position = 0
        elif position == -1:
            if z < exit_z or z < -stop_z:
                position = 0

        signal_y.iloc[i] = 0.5 * position
        signal_x.iloc[i] = -0.5 * position

    return pd.DataFrame({
        "spread": spread,
        "z_score": z_score,
        "spread_mean": spread_mean,
        "spread_std": spread_std,
        "signal_y": signal_y,
        "signal_x": signal_x,
        "position": signal_y * 2,  # 1=long spread, -1=short spread, 0=flat
    })
```

### Z-Score Threshold Configuration Guide

| Parameter | Conservative | Standard | Aggressive | Notes |
|------|------|------|------|------|
| entry_z | 2.5 | 2.0 | 1.5 | Higher threshold means fewer trades |
| exit_z | 0.3 | 0.5 | 0.8 | Higher threshold means shorter holding periods |
| stop_z | 3.0 | 3.5 | 4.0 | Beyond this level, cointegration may have broken |
| lookback | 90 | 60 | 30 | Usually 2-3× half-life |

### Spread-Stability Monitoring

```python
def monitor_spread_health(
    spread: pd.Series,
    original_half_life: float,
    original_corr: float,
    warning_hl_multiple: float = 2.0,
    warning_corr_drop: float = 0.2,
) -> dict:
    """Monitor spread stability and judge whether cointegration still holds.

    Args:
        spread: Live spread series
        original_half_life: Half-life at entry, in days
        original_corr: Correlation at entry
        warning_hl_multiple: Warn if half-life exceeds this multiple of the original
        warning_corr_drop: Warn if correlation drops by more than this amount

    Returns:
        Health-status report
    """
    recent = spread.iloc[-60:] if len(spread) > 60 else spread

    current_hl = compute_half_life(recent)
    current_adf = adfuller(recent.dropna())[1]

    hl_ratio = current_hl / original_half_life if original_half_life > 0 else float("inf")

    # Cointegration health score
    health_score = 100
    warnings = []

    if current_adf > 0.10:
        health_score -= 40
        warnings.append(f"Spread ADF p={current_adf:.3f} > 0.10, stationarity has weakened")

    if hl_ratio > warning_hl_multiple:
        health_score -= 30
        warnings.append(
            f"Half-life {current_hl:.1f}d is {hl_ratio:.1f}x the original {original_half_life:.1f}d"
        )

    if current_adf > 0.20:
        health_score -= 20
        warnings.append("Spread may no longer be stationary. Re-test cointegration immediately")

    status = "healthy" if health_score >= 70 else "warning" if health_score >= 40 else "danger"

    return {
        "health_score": health_score,
        "status": status,
        "current_half_life": round(current_hl, 1),
        "hl_ratio": round(hl_ratio, 2),
        "spread_adf_p": round(current_adf, 4),
        "warnings": warnings,
        "action": "hold" if status == "healthy" else "reduce" if status == "warning" else "exit_now",
    }
```

---

## Visualization Templates

### Rolling-Correlation Time-Series Plot

```python
import matplotlib.pyplot as plt

def plot_rolling_correlation(
    rolling_corrs: pd.DataFrame,
    title: str = "Rolling Correlation",
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """Plot rolling correlation time series across multiple windows."""
    fig, ax = plt.subplots(figsize=figsize)
    colors = ["#2196F3", "#FF9800", "#4CAF50"]
    for i, col in enumerate(rolling_corrs.columns):
        ax.plot(rolling_corrs.index, rolling_corrs[col],
                label=col, color=colors[i % len(colors)], alpha=0.8)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax.axhline(0.6, color="green", linestyle=":", linewidth=0.8, label="high-correlation threshold (0.6)")
    ax.axhline(-0.6, color="red", linestyle=":", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel("Correlation")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig
```

### Z-Score Signal Plot

```python
def plot_zscore_signals(
    signal_df: pd.DataFrame,
    entry_z: float = 2.0,
    stop_z: float = 3.5,
    figsize: tuple = (14, 8),
) -> plt.Figure:
    """Plot spread Z-Score and pair-trading signals."""
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # Top chart: spread
    axes[0].plot(signal_df["spread"], label="Spread", color="#1565C0")
    axes[0].plot(signal_df["spread_mean"], label="Mean", color="orange", linestyle="--")
    axes[0].fill_between(signal_df.index,
                         signal_df["spread_mean"] - signal_df["spread_std"],
                         signal_df["spread_mean"] + signal_df["spread_std"],
                         alpha=0.2, color="orange", label="±1σ")
    axes[0].set_title("Spread and Mean")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Bottom chart: Z-Score + signals
    axes[1].plot(signal_df["z_score"], label="Z-Score", color="#1565C0")
    axes[1].axhline(entry_z, color="red", linestyle="--", label=f"entry threshold (±{entry_z})")
    axes[1].axhline(-entry_z, color="red", linestyle="--")
    axes[1].axhline(stop_z, color="darkred", linestyle=":", label=f"stop threshold (±{stop_z})")
    axes[1].axhline(-stop_z, color="darkred", linestyle=":")
    axes[1].axhline(0, color="black", linestyle="-", linewidth=0.8)

    # Annotate entry / exit points
    long_entry = signal_df["position"].diff() > 0
    short_entry = signal_df["position"].diff() < 0
    exit_pos = (signal_df["position"] == 0) & (signal_df["position"].shift(1) != 0)

    axes[1].scatter(signal_df.index[long_entry], signal_df["z_score"][long_entry],
                    color="green", marker="^", s=80, label="long spread", zorder=5)
    axes[1].scatter(signal_df.index[short_entry], signal_df["z_score"][short_entry],
                    color="red", marker="v", s=80, label="short spread", zorder=5)
    axes[1].scatter(signal_df.index[exit_pos], signal_df["z_score"][exit_pos],
                    color="gray", marker="o", s=40, label="exit", zorder=5)

    axes[1].set_title("Z-Score and Trading Signals")
    axes[1].legend(loc="best")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
```

---

## Dependencies

```bash
pip install pandas numpy scipy statsmodels matplotlib seaborn
```

---

## Output Format

```markdown
## Correlation and Cointegration Analysis Report

### Pair: [Asset A] vs [Asset B] ([Start Date] - [End Date])

#### Correlation Statistics
| Metric | Value | Interpretation |
|------|------|------|
| Pearson r | 0.82 | Strong linear positive correlation |
| Spearman ρ | 0.80 | Consistent monotonic relationship |
| Beta (A/B) | 1.15 | Sensitivity of A to B |
| R² | 0.67 | 67% of return variance in A is explained by B |

#### Cointegration Tests
| Method | Statistic | p-value | Conclusion |
|------|--------|------|------|
| Engle-Granger | -4.12 | 0.008 | Cointegrated ** |
| Johansen trace test | 28.3 | — | 1 cointegrating vector |
| Spread ADF | -3.95 | 0.002 | Spread is stationary ** |

#### Mean-Reversion Characteristics
| Metric | Value |
|------|------|
| OLS hedge ratio | 1.23 |
| Half-life | 18.5 days |
| Suggested holding window | 10-30 days |
| Suggested lookback window | 40-60 days |

#### Conditional Correlation (Regime Analysis)
| Regime | Correlation | Sample Size |
|------|---------|--------|
| Bull | 0.76 | 312 days |
| Bear | 0.88 | 198 days |
| High volatility | 0.91 | 87 days |
| Sideways | 0.71 | 645 days |

#### Recommended Pair-Trading Signal Parameters
| Parameter | Value |
|------|-----|
| entry_z | 2.0 |
| exit_z | 0.5 |
| stop_z | 3.5 |
| lookback | 60 days |

#### Current Spread Status
| Metric | Value | Alert |
|------|-----|------|
| Current Z-Score | -2.3 | Near entry zone |
| Health score | 85/100 | Healthy |
| Half-life (last 60 days) | 21.2 days | Normal |
```

---

## Notes

1. **Prices vs returns**: Use price series, which are non-stationary, for cointegration tests; use return series, which are stationary, for correlation analysis. Mixing them is the most common mistake.
2. **Data alignment**: Cross-market analysis must handle holiday mismatches with an inner join. Do not forward-fill missing trading days, or you will create fake correlation.
3. **Cointegration is not the same as high correlation**: Two series can have Pearson < 0.3 and still be cointegrated, and the reverse can also happen.
4. **Out-of-sample validation**: If a pair is selected using cointegration on the first N years, you must verify whether the relationship survives in later out-of-sample data to avoid overfitting.
5. **Crisis-period risk**: Correlation jumps in crises, and both legs in a pair can crash together. Stop thresholds should be tighter than in normal periods.
6. **China A-share specifics**: China A-shares contain many non-trading days due to holidays and suspensions. Date alignment is especially important in cross-market comparison.
7. **Multiple testing**: When testing N asset pairs simultaneously, use Benjamini-Hochberg FDR adjustment on p-values. Otherwise false positives will be excessive.
8. **Kalman tuning**: Tune `delta` with grid search plus out-of-sample validation. Do not rely blindly on the default value.
