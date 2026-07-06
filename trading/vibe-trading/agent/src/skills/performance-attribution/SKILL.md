---
name: performance-attribution
description: Performance attribution analysis — Brinson sector/stock-selection attribution, factor alpha/beta decomposition, market-timing evaluation, and benchmark comparison framework.
category: analysis
---

# Performance Attribution Analysis

## Overview

Decompose portfolio excess returns into explainable sources: sector allocation, stock selection, factor exposure, timing contribution, and more. This helps explain **why** a strategy made or lost money, rather than only **how much** it made or lost.

## Brinson Attribution Model

### Single-Period Brinson-Fachler Model

```
Total excess return = portfolio return - benchmark return

Decomposed into three parts:
1. Allocation effect: sector-weight deviation × sector benchmark return deviation
2. Selection effect: stock selection within a sector × sector benchmark weight
3. Interaction effect: weight deviation × stock-selection deviation
```

**Mathematical formulas**:

```
Let w_p,i = portfolio weight of sector i
    w_b,i = benchmark weight of sector i
    r_p,i = portfolio return of sector i
    r_b,i = benchmark return of sector i
    R_b   = total benchmark return

Allocation_i = (w_p,i - w_b,i) × (r_b,i - R_b)
Selection_i  = w_b,i × (r_p,i - r_b,i)
Interaction_i = (w_p,i - w_b,i) × (r_p,i - r_b,i)

Total excess = Σ(Allocation_i) + Σ(Selection_i) + Σ(Interaction_i)
```

### Example Brinson Attribution

```markdown
### Brinson Sector Attribution

| Sector | Portfolio Weight | Benchmark Weight | Portfolio Return | Benchmark Return | Allocation | Selection | Interaction |
|------|---------|---------|---------|---------|---------|---------|---------|
| Food & Beverage | 20% | 10% | 15% | 8% | +0.3% | +0.7% | +0.7% |
| Electronics | 15% | 12% | 5% | 10% | -0.1% | -0.6% | +0.2% |
| Banks | 5% | 20% | 3% | 2% | +0.3% | +0.2% | -0.2% |
| Others | 60% | 58% | 8% | 7% | +0.0% | +0.6% | +0.0% |
| **Total** | 100% | 100% | 9.5% | 6.2% | **+0.5%** | **+0.9%** | **+0.7%** |

Excess return 3.3% = allocation effect 0.5% + selection effect 0.9% + interaction effect 0.7% + residual 0.2%
```

### Multi-Period Attribution (Linked Brinson)

```
Directly summing single-period attribution creates residuals (compounding effect). Common approaches:

Method 1: arithmetic linking (simple sum of each period's attribution)
  - Advantage: simple
  - Disadvantage: residual remains

Method 2: Carino logarithmic linking
  - Advantage: no residual
  - Disadvantage: more complex

Practical recommendation: arithmetic linking is enough for monthly attribution; residuals are usually <0.1%
```

## Factor Attribution

### Alpha-Beta Decomposition

```
R_p = α + β × R_m + ε

α (alpha): excess return, manager skill
β (beta): market exposure, systematic risk
ε (epsilon): residual, idiosyncratic risk

Regression method: OLS regression, with at least 60 data points
```

#### Multi-Factor Attribution (Fama-French Extension)

```
R_p - R_f = α + β_mkt × (R_m - R_f) + β_smb × SMB + β_hml × HML + β_mom × MOM + ε

| Factor | Meaning | China A-share Proxy |
|------|------|--------|
| MKT | Market | CSI 300 return |
| SMB | Small-cap premium | CSI 500 - CSI 300 |
| HML | Value premium | high-PB group - low-PB group |
| MOM | Momentum | top past-12M winners - bottom group |
```

#### Factor Exposure Analysis Template

```markdown
### Factor Exposure Analysis

| Factor | Beta | t-stat | Significance | Interpretation |
|------|------|---------|--------|------|
| Market (MKT) | 0.85 | 12.3 | *** | Below 1, defensive profile |
| Small-cap (SMB) | 0.25 | 3.2 | ** | Small-cap tilt |
| Value (HML) | -0.15 | -1.8 | * | Growth tilt |
| Momentum (MOM) | 0.30 | 4.1 | *** | Significant momentum exposure |
| **Alpha** | **0.8% / month** | **2.5** | ** | **Significant alpha** |

R² = 0.72 → factors explain 72% of return variation
Alpha = 0.8% / month = 10% / year, significant
```

## Market-Timing Evaluation

### Treynor-Mazuy Model

```
R_p - R_f = α + β × (R_m - R_f) + γ × (R_m - R_f)² + ε

γ > 0 and significant → timing ability exists (adds risk in bull markets, cuts risk in bear markets)
γ ≤ 0 → no timing ability
```

### Henriksson-Merton Model

```
R_p - R_f = α + β × (R_m - R_f) + γ × max(R_m - R_f, 0) + ε

γ > 0 → portfolio beta is higher in bull markets (successful timing)
```

### Practical Timing Metrics

| Metric | Calculation | Meaning |
|------|------|------|
| Bull capture ratio | portfolio return in bull markets / benchmark return | >100% = outperforming |
| Bear capture ratio | portfolio return in bear markets / benchmark return | <100% = better downside defense |
| Timing hit rate | proportion of months where market direction was called correctly | >55% = shows skill |
| Correlation between position changes and market | `corr(position_change, future_return)` | >0 = timing is correct |

## Benchmark Comparison Framework

### Benchmark Selection

| Strategy Type | Recommended Benchmark | China A-share Code |
|---------|---------|---------|
| China A-share large cap | CSI 300 | 000300.SH |
| China A-share small cap | CSI 500 / CSI 1000 | 000905.SH |
| China A-share broad market | CSI All Share | 000985.SH |
| Hong Kong equities | Hang Seng Index | HSI |
| US equities | S&P 500 | SPX |
| Crypto | BTC | BTC-USDT |
| Multi-asset | 60/40 portfolio | self-constructed |

### Risk-Adjusted Performance Metrics

| Metric | Formula | Excellent | Good | Average |
|------|------|------|------|------|
| Sharpe | `(R_p - R_f) / σ_p` | >1.5 | 1.0-1.5 | 0.5-1.0 |
| Sortino | `(R_p - R_f) / σ_down` | >2.0 | 1.5-2.0 | 1.0-1.5 |
| Calmar | `R_p / MaxDD` | >1.0 | 0.5-1.0 | 0.2-0.5 |
| Information Ratio | `(R_p - R_b) / TE` | >1.0 | 0.5-1.0 | 0.2-0.5 |
| Treynor | `(R_p - R_f) / β` | used comparatively | | |

### Rolling Analysis

```
Use rolling windows (such as 12 months) to analyze:
- Rolling Sharpe: strategy stability
- Rolling alpha: whether alpha persists
- Rolling beta: whether market exposure is stable
- Rolling information ratio: persistence of benchmark outperformance

Suggested windows: 252 days for daily data, 12-36 months for monthly data
```

## Analysis Framework

### Step 1: Aggregate Analysis

```
1. Cumulative return vs benchmark
2. Excess-return decomposition (annual / monthly)
3. Summary risk metrics (volatility / max drawdown / Sharpe)
```

### Step 2: Attribution Decomposition

```
1. Brinson attribution (if sector information is available)
2. Factor attribution (alpha / beta / factor exposure)
3. Timing attribution (TM / HM models)
```

### Step 3: Style Analysis

```
1. Large cap vs small cap exposure
2. Growth vs value exposure
3. Style drift detection (rolling style analysis)
```

### Step 4: Conclusions and Recommendations

```
1. Main sources of excess return
2. Whether risk exposure is reasonable
3. Suggested improvement directions
```

## Output Format

```markdown
## Performance Attribution Report

### Performance Overview
| Metric | Strategy | Benchmark | Excess |
|------|------|------|------|
| Cumulative return | +85.2% | +32.1% | +53.1% |
| Annualized return | 12.5% | 5.8% | +6.7% |
| Annualized volatility | 18.2% | 20.5% | - |
| Sharpe | 0.69 | 0.28 | - |
| Information Ratio | 0.82 | - | - |

### Attribution Breakdown
| Source | Contribution (annualized) | Share |
|------|-----------|------|
| Sector allocation | +2.1% | 31% |
| Stock selection | +3.8% | 57% |
| Timing | +0.8% | 12% |

### Factor Exposure
[factor exposure table]

### Conclusion
Excess return mainly comes from stock selection (57% contribution), followed by sector allocation.
Alpha is significant (`t=2.5`), indicating real stock-picking ability.
Watch the risk of excessive small-cap exposure (`SMB beta=0.25`).
```

## Notes

1. **Attribution ≠ prediction**: attribution explains the past; it does not guarantee persistence in the future
2. **Benchmark selection affects attribution**: switch the benchmark and alpha may disappear, so benchmark choice must be appropriate
3. **Data frequency**: daily attribution is noisy, monthly attribution is more stable but has fewer samples; recommended workflow is daily computation with monthly reporting
4. **Survivorship bias**: delisted stocks may be excluded in backtests, creating false alpha
5. **Multiple-testing problem**: if you test 100 strategies, about 5 may appear significant by chance (`p=0.05`); use multiple-comparison correction
6. **Factor data requirement**: factor attribution requires factor return data, which can be obtained from `tushare` or self-constructed
7. **Attribution in backtest reports**: `metrics.csv` already provides basic metrics after a backtest; this skill adds deeper attribution analysis
