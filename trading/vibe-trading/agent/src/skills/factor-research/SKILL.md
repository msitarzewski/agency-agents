---
name: factor-research
description: Factor research framework with IC/IR analysis, quantile backtesting, and factor combination. Suitable for cross-sectional factor evaluation across multiple instruments.
category: analysis
---

# Factor Research Framework

## Purpose

Systematically evaluates the predictive power of single or multiple factors. Uses IC/IR statistical tests and quantile backtests to determine whether a factor has stock-selection power, and to guide factor screening and combination.

Applicable scenarios:
- Single-factor validity testing (momentum, value, quality, volatility, and more)
- Determining weights for multi-factor combination
- Factor decay analysis (IC changes across different holding periods)
- Comparing factor differences across industries and markets

## Workflow

1. **Calculate factor values**: compute factor exposures for each instrument on the cross-section, and output a factor CSV (`index=date`, `columns=codes`)
2. **Calculate returns**: compute each instrument's forward N-day return, and output a return CSV (same structure)
3. **Call the `factor_analysis` tool**: pass in the factor CSV, return CSV, and output directory
4. **Interpret the results**: judge factor validity based on IC/IR criteria and quantile backtest results
5. **Factor screening / combination**: keep effective factors and combine them with equal weights or IC-based weights

**Key point**: the rows (dates) and columns (instrument codes) of the factor CSV and return CSV must align exactly. Returns must be forward returns after the factor-observation date (to avoid look-ahead bias).

## `factor_analysis` Tool Parameters

| Parameter | Type | Required | Default | Description |
|------|------|------|------|------|
| factor_csv | string | Yes | - | Path to the factor-value CSV |
| return_csv | string | Yes | - | Path to the return CSV |
| output_dir | string | Yes | - | Output directory for results |
| n_groups | integer | No | 5 | Number of quantile groups |

## Output Files

| File | Contents |
|------|------|
| ic_series.csv | Daily IC series |
| ic_summary.json | IC mean, IC standard deviation, IR, proportion of IC > 0 |
| group_equity.csv | Cumulative equity curves for each quantile group |

## IC/IR Interpretation Standards

| Metric | Threshold | Interpretation |
|------|------|------|
| IC mean | > 0.03 | Factor has basic predictive power |
| IC mean | > 0.05 | Factor has strong predictive power |
| IC mean | > 0.10 | Unusually high; check for look-ahead bias |
| IR (IC mean / IC std) | > 0.5 | Factor is stably effective |
| IR | > 1.0 | Extremely strong, very rare |
| Proportion of IC > 0 | > 55% | Factor direction is stable |
| Proportion of IC > 0 | < 50% | Factor direction is unstable and unusable |

Note: negative IC can also be useful (reverse factors). Judge by absolute value, and reverse the signal direction in actual use.

## Quantile Backtest Interpretation

Quantile backtesting sorts instruments into N groups by factor value from low to high (default 5 groups), with equal-weight holding inside each group.

**Criteria**:
- **Monotonicity**: the final net values from `Group_1` to `Group_N` should show a monotonic rising (or falling) pattern. Better monotonicity means stronger factor discrimination
- **Long-short spread**: the net-value difference between the highest and lowest group (`long_short_spread`). A larger spread means stronger selection power
- **Nonlinearity**: if only the top and bottom groups differ materially while the middle groups are similar, the factor may only be effective in the tails
- **Stability**: group equity curves should be smooth; sharp swings indicate an unstable factor

**Warning signs**:
- No meaningful difference across group equity curves → the factor is ineffective
- Non-monotonic pattern (such as V-shape or inverted V-shape) → the factor may have a nonlinear relationship and requires further analysis
- One group's net value falls persistently → the factor may be usable in reverse

## Factor Combination Methods

When multiple single factors pass validity tests, they should be combined into a composite factor:

### Equal-Weight Combination
The simplest method: standardize each factor and sum them with equal weights. Suitable when the factor count is small and IC differences are minor.

```
Composite factor = Z(factor1) + Z(factor2) + ... + Z(factorN)
where Z() is cross-sectional Z-score standardization
```

### IC-Weighted Combination
Assign weights according to historical IC mean. Factors with higher IC receive larger weights.

```
weight_i = |IC_mean_i| / sum(|IC_mean_j|)
Composite factor = sum(weight_i * Z(factor_i))
```

### Orthogonalized Combination
First orthogonalize the factors with the Schmidt process to remove collinearity, then combine them with equal weights. Suitable when factors are highly correlated with one another.

```
1. Sort factors by IC from high to low
2. Keep the first factor unchanged
3. Regress each later factor on all previous factors and use the residual as the orthogonalized factor
4. Combine the orthogonalized factors with equal weights
```

## Common Pitfalls

### Look-Ahead Bias
- Factor values must be computed using data from day T and earlier, while returns must use data from T+1 to T+N
- Wrong example: calculate the factor with day T closing price and correlate it with day T return → artificially inflated IC
- Correct approach: factor value at day T, return defined as the move from the T close to the T+1 close and beyond

### Skewed Factor Distributions
- Some factors (such as market cap and turnover) have heavily right-skewed distributions
- Computing IC directly from raw values makes the result dominated by outliers
- Solution: apply cross-sectional rank or Z-score standardization before computing IC

### Industry Neutralization
- Factor values can be highly similar within the same industry, causing stock selection to cluster in a few sectors
- Solution: perform Z-score standardization within each industry (industry neutralization) to remove industry effects
- For China A-shares, Shenwan Level-1 industries can be used

### Insufficient Sample Size
- Each cross-section should contain at least 5 valid instruments to compute meaningful IC
- Quantile backtests require at least `n_groups` instruments
- When the universe is too small, IC is noisy and IR becomes unreliable

### Factor Crowding
- Classic factors (momentum, value) may see diminished excess returns after becoming widely used
- Regularly inspect the time-series evolution of factor IC to see whether decay is occurring
- Consider factor innovation or factor timing

### Survivorship Bias
- Backtesting only on stocks that still survive today will overestimate factor performance
- Use full-sample data including delisted stocks

## Dependencies

```bash
pip install pandas numpy scipy
```

## Calling Zoo Factors

Rather than recompute factors from raw OHLCV every research iteration, prefer reusing the 450+ pre-built alphas in the Alpha Zoo registry. Each alpha is metadata-validated (`AlphaMeta` schema with `theme`, `universe`, `columns_required`, `decay_horizon`, `min_warmup_bars`), shape-checked against `panel["close"]`, and rejected if it emits `+/- inf` or >95% NaN — so the factor CSV you feed to `factor_analysis` is already sanity-checked.

```python
from src.factors.registry import Registry

registry = Registry()
ids = registry.list(theme="momentum", universe="equity_cn")  # filter the catalogue
factor_panel = registry.compute("alpha101_001", panel)        # wide DataFrame, same shape as panel["close"]
factor_panel.to_csv("factor_alpha101_001.csv")                # ready for factor_analysis tool
```

For combining several validated alphas into one composite signal, see the `multi-factor` skill's `ZooSignalEngine` (it z-scores, weights, and ranks alphas for you, with per-alpha skip isolation). For browsing the catalogue and inspecting individual `__alpha_meta__` records, see the `alpha-zoo` skill.

