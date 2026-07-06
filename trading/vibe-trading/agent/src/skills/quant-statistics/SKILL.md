---
name: quant-statistics
description: "Quantitative statistical methods: ADF unit-root / cointegration tests, GARCH volatility modeling, regression diagnostics (heteroskedasticity / autocorrelation), Bootstrap, and hypothesis testing."
category: analysis
---

# Quantitative Statistical Methods

## Overview

Common statistical methodology used in quantitative investing, covering time-series testing, volatility modeling, regression diagnostics, and statistical inference. Provides the statistical foundation for strategy development and factor research.

## Time-Series Tests

### 1. ADF Unit-Root Test (Stationarity Test)

**Why it matters**: regressing non-stationary series directly can produce spurious regression, making conclusions unreliable.

```python
from statsmodels.tsa.stattools import adfuller

def adf_test(series: pd.Series, significance: float = 0.05) -> dict:
    """
    ADF test: H0 = unit root exists (non-stationary), H1 = stationary

    Args:
        series: Time series
        significance: Significance level
    Returns:
        Test result
    """
    result = adfuller(series.dropna(), autolag='AIC')
    return {
        'adf_statistic': result[0],
        'p_value': result[1],
        'lags_used': result[2],
        'is_stationary': result[1] < significance,
        'critical_values': result[4],  # 1%, 5%, 10%
    }
```

**Decision rules**:

| p-value | Conclusion | Action |
|-----|------|------|
| < 0.01 | Strongly stationary | Can be used directly for regression / modeling |
| 0.01-0.05 | Stationary | Usable |
| 0.05-0.10 | Weak evidence | Difference the series and retest |
| > 0.10 | Non-stationary | Must difference or handle with cointegration |

**Stationarity of common financial series**:

| Series | Typical Result | Treatment |
|------|---------|---------|
| Price series | Non-stationary (unit root) | Use log returns |
| Log returns | Stationary | Can be used directly |
| PE / PB series | Usually non-stationary | Use changes or logs |
| Volatility series | Usually stationary | Can be used directly |
| Volume | May be non-stationary | Use logs or standardization |

### 2. Cointegration Test

**Purpose**: determine whether two non-stationary series share a long-run equilibrium relationship (the foundation of pair trading / statistical arbitrage).

```python
from statsmodels.tsa.stattools import coint

def cointegration_test(y: pd.Series, x: pd.Series) -> dict:
    """
    Engle-Granger two-step cointegration test
    H0: no cointegration relationship

    Args:
        y, x: Two price series
    Returns:
        Test result
    """
    score, p_value, critical = coint(y, x)
    return {
        'test_statistic': score,
        'p_value': p_value,
        'is_cointegrated': p_value < 0.05,
        'critical_values': {'1%': critical[0], '5%': critical[1], '10%': critical[2]},
    }
```

**Application in pair trading**:

```python
import statsmodels.api as sm

def find_hedge_ratio(y: pd.Series, x: pd.Series) -> dict:
    """
    Compute hedge ratio: y = α + β×x + ε
    Spread = y - β×x
    """
    x_const = sm.add_constant(x)
    model = sm.OLS(y, x_const).fit()

    spread = y - model.params[1] * x

    return {
        'hedge_ratio': model.params[1],
        'intercept': model.params[0],
        'spread_mean': spread.mean(),
        'spread_std': spread.std(),
        'half_life': compute_half_life(spread),  # mean-reversion speed
    }

def compute_half_life(spread: pd.Series) -> float:
    """Estimate half-life with OLS regression."""
    spread_lag = spread.shift(1)
    delta = spread - spread_lag
    model = sm.OLS(delta.dropna(), sm.add_constant(spread_lag.dropna())).fit()
    half_life = -np.log(2) / model.params[1]
    return half_life
```

**Pair-trading signal**:

```
z_score = (spread - mean) / std

| z_score | Signal |
|---------|------|
| > 2.0 | Short spread (sell y, buy x) |
| > 1.5 | Small short spread |
| < -1.5 | Small long spread |
| < -2.0 | Long spread (buy y, sell x) |
| Back near 0 | Close position |
```

### 3. Granger Causality Test

```python
from statsmodels.tsa.stattools import grangercausalitytests

def granger_test(data: pd.DataFrame, x_col: str, y_col: str, max_lag: int = 5):
    """
    Test whether x Granger-causes y (whether historical x helps predict y).
    Note: Granger causality is not true causality, only predictive causality.
    """
    results = grangercausalitytests(data[[y_col, x_col]].dropna(), maxlag=max_lag)
    return {lag: results[lag][0]['ssr_ftest'][1] for lag in range(1, max_lag+1)}
```

## GARCH Volatility Modeling

### GARCH(1,1) Model

```
Returns: r_t = μ + ε_t
Volatility: σ²_t = ω + α×ε²_{t-1} + β×σ²_{t-1}

Parameter meanings:
- ω (omega): long-run variance baseline
- α (alpha): impact of yesterday's shock on today's volatility
- β (beta): persistence of yesterday's volatility into today
- α + β: volatility persistence (usually 0.95-0.99)
- Long-run volatility = sqrt(ω / (1 - α - β))
```

```python
from arch import arch_model

def fit_garch(returns: pd.Series) -> dict:
    """
    Fit a GARCH(1,1) model.

    Args:
        returns: Daily return series (in percentage form)
    Returns:
        Model parameters and forecasts
    """
    model = arch_model(returns * 100, vol='Garch', p=1, q=1,
                       mean='Constant', dist='normal')
    result = model.fit(disp='off')

    # Forecast volatility for the next 5 days
    forecast = result.forecast(horizon=5)

    return {
        'omega': result.params['omega'],
        'alpha': result.params['alpha[1]'],
        'beta': result.params['beta[1]'],
        'persistence': result.params['alpha[1]'] + result.params['beta[1]'],
        'long_run_vol': np.sqrt(result.params['omega'] /
                        (1 - result.params['alpha[1]'] - result.params['beta[1]'])) / 100,
        'current_vol': np.sqrt(result.conditional_volatility[-1]) / 100,
        'forecast_vol_5d': np.sqrt(forecast.variance.values[-1, :]) / 100,
        'aic': result.aic,
        'bic': result.bic,
    }
```

### GARCH Variants

| Model | Characteristics | Applicable Scenario |
|------|------|---------|
| GARCH(1,1) | Baseline, symmetric shock response | Default choice |
| EGARCH | Asymmetric (leverage effect) | Down-move volatility > up-move volatility |
| GJR-GARCH | Another asymmetric form | Same use case as EGARCH, easier to interpret |
| FIGARCH | Long memory | Volatility clustering persists for very long periods |

**GARCH characteristics in China A-shares / crypto**:

```
China A-shares:
- α usually 0.05-0.15
- β usually 0.80-0.90
- Clear leverage effect (EGARCH fits better)
- Strong volatility clustering persistence

BTC:
- α usually 0.05-0.20 (shocks matter more)
- β usually 0.75-0.90
- More symmetric shocks (little difference between up/down volatility)
- Long-run volatility around 60-80% annualized
```

## Regression Diagnostics

### 1. Heteroskedasticity Test

```python
from statsmodels.stats.diagnostic import het_white, het_breuschpagan

def heteroscedasticity_test(model_result) -> dict:
    """
    Test whether residuals are heteroskedastic.
    H0: homoskedasticity
    """
    # White test
    white_stat, white_p, _, _ = het_white(model_result.resid, model_result.model.exog)

    # BP test
    bp_stat, bp_p, _, _ = het_breuschpagan(model_result.resid, model_result.model.exog)

    return {
        'white_p': white_p,
        'bp_p': bp_p,
        'has_heteroscedasticity': white_p < 0.05 or bp_p < 0.05,
        'fix': 'Use HAC standard errors (Newey-West) or WLS' if white_p < 0.05 else 'No adjustment needed',
    }
```

**Heteroskedasticity fixes**:
- Use `model.fit(cov_type='HAC', cov_kwds={'maxlags': 5})`
- Or use weighted least squares (WLS)
- Financial data is almost always heteroskedastic -> use HAC standard errors by default

### 2. Autocorrelation Test

```python
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson

def autocorrelation_test(residuals: pd.Series, lags: int = 10) -> dict:
    """
    Test whether residuals are autocorrelated.
    H0: no autocorrelation
    """
    # DW test (first-order only)
    dw = durbin_watson(residuals)

    # Ljung-Box test (multiple lags)
    lb_result = acorr_ljungbox(residuals, lags=lags)

    return {
        'durbin_watson': dw,
        'dw_interpretation': 'positive autocorrelation' if dw < 1.5 else 'no autocorrelation' if dw < 2.5 else 'negative autocorrelation',
        'ljung_box_p': lb_result['lb_pvalue'].values,
        'has_autocorrelation': any(lb_result['lb_pvalue'] < 0.05),
        'fix': 'Use Newey-West standard errors or include lag terms',
    }
```

### 3. Multicollinearity Test

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

def vif_test(X: pd.DataFrame) -> pd.DataFrame:
    """
    VIF test for multicollinearity
    VIF > 10 -> severe collinearity
    VIF > 5 -> needs attention
    """
    vif_data = pd.DataFrame()
    vif_data['feature'] = X.columns
    vif_data['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    vif_data['concern'] = vif_data['VIF'].apply(
        lambda x: 'severe' if x > 10 else 'watch' if x > 5 else 'normal'
    )
    return vif_data
```

### Regression Diagnostics Checklist

```
□ 1. Linearity: residuals vs fitted values show no obvious pattern
□ 2. Normality: residual QQ plot is close to a straight line, Jarque-Bera p>0.05
□ 3. Heteroskedasticity: White / BP test p>0.05, or use HAC standard errors
□ 4. Autocorrelation: DW≈2, Ljung-Box p>0.05
□ 5. Multicollinearity: VIF<5
□ 6. Outliers: Cook's D < 4/n
```

## Bootstrap Methods

### Nonparametric Bootstrap

```python
def bootstrap_statistic(data: np.ndarray, statistic_func,
                        n_bootstrap: int = 10000,
                        confidence: float = 0.95) -> dict:
    """
    Estimate a confidence interval for a statistic with Bootstrap.

    Args:
        data: Raw data
        statistic_func: Statistic function (for example np.mean, np.median)
        n_bootstrap: Number of Bootstrap resamples
        confidence: Confidence level
    Returns:
        Point estimate and confidence interval
    """
    n = len(data)
    bootstrap_stats = np.array([
        statistic_func(np.random.choice(data, size=n, replace=True))
        for _ in range(n_bootstrap)
    ])

    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, alpha/2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha/2) * 100)

    return {
        'point_estimate': statistic_func(data),
        'bootstrap_mean': np.mean(bootstrap_stats),
        'bootstrap_std': np.std(bootstrap_stats),
        'ci_lower': lower,
        'ci_upper': upper,
        'confidence': confidence,
    }
```

### Bootstrap Applications in Quant

| Scenario | Method | Purpose |
|------|------|------|
| Sharpe-ratio confidence interval | Bootstrap return series | Determine whether Sharpe is significantly >0 |
| Factor return test | Bootstrap factor values | Whether factor premium is robust |
| Maximum drawdown distribution | Bootstrap equity paths | Probability distribution of max drawdown |
| Strategy comparison | Paired Bootstrap | Whether strategy A is significantly better than B |

```python
def bootstrap_sharpe(returns: pd.Series, n_bootstrap: int = 10000) -> dict:
    """Bootstrap confidence interval for the Sharpe ratio."""
    def sharpe(r):
        return r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0

    result = bootstrap_statistic(returns.values, sharpe, n_bootstrap)
    result['is_significant'] = result['ci_lower'] > 0  # 95% CI excludes 0
    return result
```

## Hypothesis-Testing Framework

### Quick Reference for Common Tests

| Testing Goal | Test Method | Null Hypothesis |
|---------|---------|--------|
| Mean = 0 | t-test | `μ = 0` |
| Two means are equal | Independent t-test | `μ1 = μ2` |
| Normality | Jarque-Bera | Normal distribution |
| Stationarity | ADF | Has unit root (non-stationary) |
| Autocorrelation | Ljung-Box | No autocorrelation |
| Heteroskedasticity | White / BP | Homoskedasticity |
| Cointegration | Engle-Granger | Not cointegrated |

### Multiple-Testing Problem

```
Problem: test 100 factors and filter with p<0.05 -> expect 5 false positives

Correction methods:
1. Bonferroni: p_adj = p × n_tests (most conservative)
2. Holm-Bonferroni: stepwise correction (fairly conservative)
3. Benjamini-Hochberg (FDR): control false discovery rate (recommended)

from statsmodels.stats.multitest import multipletests
reject, p_adj, _, _ = multipletests(p_values, method='fdr_bh')
```

### Statistical Significance in Financial Backtests

```
Sharpe significance test:
H0: Sharpe = 0 (strategy is ineffective)
H1: Sharpe > 0

Test statistic: t = Sharpe × sqrt(n) / sqrt(1 + 0.5×Sharpe²)
where n = number of observation periods (years)

Rules of thumb:
- Sharpe > 0.5 and backtest >5 years -> may be significant
- Sharpe > 1.0 and backtest >3 years -> likely significant
- Sharpe > 2.0 -> overfitting warning (hard to sustain in reality)
```

## Output Format

```markdown
## Statistical Testing Report

### Stationarity Test
| Series | ADF Statistic | p-value | Conclusion |
|------|----------|-----|------|
| Price | -1.23 | 0.65 | Non-stationary |
| Return | -15.8 | 0.000 | Stationary *** |

### Cointegration Test
| Pair | Statistic | p-value | Cointegrated |
|------|--------|-----|------|
| 600519/000858 | -4.52 | 0.002 | Yes ** |

### GARCH Model
| Parameter | Value | Meaning |
|------|-----|------|
| α | 0.08 | Shock effect |
| β | 0.88 | Volatility persistence |
| Long-run volatility | 22.5% | Annualized |

### Bootstrap Result
| Metric | Point Estimate | 95% CI | Significant |
|------|--------|--------|------|
| Sharpe | 1.25 | [0.62, 1.88] | Yes |
| Alpha (monthly) | 0.8% | [0.1%, 1.5%] | Yes |
```

## Notes

1. **Financial data is non-normal**: almost all financial return series are fat-tailed, so be careful with tests assuming normality
2. **Multiple testing**: when backtesting many strategies / factors, multiple-testing correction (FDR control) is mandatory
3. **Out-of-sample validation**: statistical significance does not guarantee profitability; out-of-sample testing is still required
4. **Cointegration can break down**: historical cointegration does not guarantee persistence, so pair trading needs ongoing monitoring
5. **GARCH forecast horizon is limited**: volatility-forecast accuracy declines rapidly beyond 5-10 days
6. **Be careful with small samples**: financial datasets may look large, but the number of independent observations can still be small (for example, annual data)
7. **p-hacking risk**: do not keep adjusting until p<0.05; predefine the testing plan
