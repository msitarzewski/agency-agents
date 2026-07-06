---
name: macro-analysis
description: Macroeconomic cycle positioning and central-bank policy interpretation, including GDP/CPI/PMI/rates/FX analysis, with output in the form of major-asset allocation tilts.
category: analysis
---

# Macroeconomic Analysis

## Overview

Interprets macroeconomic data and central-bank policy, identifies the current economic-cycle stage, and derives major-asset allocation direction. Covers the three major economies of China (PBOC), the United States (Fed), and Europe (ECB).

## Core Indicator System

### Growth Indicators

| Indicator | Frequency | Key Threshold | Data Source |
|------|------|----------|--------|
| GDP YoY | Quarterly | China >5% = normal, <4% = weak | National Bureau of Statistics |
| Manufacturing PMI | Monthly | >50 = expansion, <50 = contraction, 49-51 = borderline | NBS / Caixin |
| Industrial production | Monthly | >5% = normal | National Bureau of Statistics |
| Retail sales | Monthly | >8% = strong consumption | National Bureau of Statistics |
| Fixed asset investment | Monthly | Focus on infrastructure vs real-estate components | National Bureau of Statistics |

### Inflation Indicators

| Indicator | Frequency | Key Threshold | Interpretation |
|------|------|----------|------|
| CPI YoY | Monthly | >3% = inflation pressure, <0% = deflation risk | Strongly affected by the pork cycle, so core CPI is more reliable |
| PPI YoY | Monthly | >0% = improving corporate profits, <0% = deflation transmission | Leads CPI by 3-6 months |
| Core CPI | Monthly | >2% = demand-driven inflation | Excludes food and energy |
| M2 YoY | Monthly | >10% = monetary easing | The M2-M1 spread reflects how active liquidity is |

### Rates and FX

| Indicator | Meaning | Focus |
|------|------|--------|
| 1Y / 5Y LPR | Loan prime rate | Rate-cut signal |
| DR007 | Interbank 7-day repo rate | Funding tightness / looseness |
| 10Y government bond yield | Risk-free rate anchor | <2.5% = loose, >3.5% = tight |
| USD/CNY | Exchange rate | >7.3 = high depreciation pressure |
| US 10Y-2Y spread | Term spread | Inversion signals recession (leads by 12-18 months) |

## Four-Stage Economic Cycle Model

### Merrill Lynch Clock Framework

```
        GDP↑ + CPI↓           GDP↑ + CPI↑
        ┌─────────┐           ┌─────────┐
        │ Recovery │ ────→    │ Overheat│
        │          │           │         │
        └────┬────┘           └────┬────┘
             ↑                     │
             │                     ↓
        ┌────┴────┐           ┌────┴────┐
        │Recession│ ←────     │Stagflat │
        │         │           │         │
        └─────────┘           └─────────┘
        GDP↓ + CPI↓           GDP↓ + CPI↑
```

### Asset Performance by Stage

| Stage | Best Asset | Second-Best Asset | Worst Asset | Typical Policy |
|------|----------|----------|----------|----------|
| Recovery | Equities (growth / small cap) | Commodities | Bonds | Monetary easing + fiscal stimulus |
| Overheat | Commodities (oil / copper) | Equities (cyclical / value) | Bonds | Hiking cycle begins |
| Stagflation | Cash / short-duration bonds | Gold | Equities | Policy dilemma |
| Recession | Bonds (long duration) | Gold | Equities / commodities | Rate cuts + quantitative easing |

### China-Specific Adjustments

- **Real-estate cycle**: property sales / investment is a core variable in China's economy, and the policy response during downturns determines the turning point
- **Infrastructure offset**: when property is weak, infrastructure often strengthens (countercyclical adjustment), so track the pace of special-bond issuance
- **Export orientation**: external demand (US PMI / Eurozone PMI) affects manufacturing conditions
- **Policy-driven market**: tone-setting from Politburo meetings / the Central Economic Work Conference matters more than the data itself

## Central Bank Policy Analysis Framework

### Federal Reserve (Fed)

**Sequence to watch**: FOMC statement → dot plot → Powell speech → meeting minutes

| Signal | Hawkish (tightening) | Dovish (easing) |
|------|-------------|-------------|
| Employment | "labor market remains tight" | "softening in labor market" |
| Inflation | "inflation remains elevated" | "inflation moving toward target" |
| Forward guidance | "further tightening may be appropriate" | "rate cuts could be appropriate" |
| Balance sheet | Faster / continued QT | Slower QT / hints of QE |

**Fed decision function**: core PCE > 2.5% → tightening bias; unemployment > 4.5% → easing bias; when the two conflict, focus on which deviation is larger

### People's Bank of China (PBOC)

**Toolbox:**

| Tool | Signal Strength | Impact |
|------|---------|------|
| RRR cut | Strong | Releases long-term liquidity, bullish for equities and bonds |
| Rate cuts (MLF/LPR) | Strong | Reduces financing costs, bullish for growth stocks |
| OMO (reverse repo) | Medium | Short-term liquidity adjustment |
| PSL / relending | Medium | Targeted support (infrastructure / real estate) |
| Window guidance | Weak but effective | Directs credit allocation |

### European Central Bank (ECB)

**Core variables**: HICP (harmonized CPI), Eurozone PMI, Germany-France yield spread
**Special feature**: large divergence among member economies, creating a "one size fits all" problem

## Analysis Framework

### Step 1: Data Collection and Current-State Description

```
Collect core indicators from the latest 3 months:
- China: PMI, CPI, PPI, M2, aggregate financing, LPR
- United States: nonfarm payrolls, CPI, core PCE, ISM PMI, Fed rate
- Global: oil, copper, US dollar index (DXY), VIX
```

### Step 2: Cycle Positioning

```
Decision criteria:
1. GDP trend: accelerating / decelerating / topping / bottoming
2. Inflation trend: rising / falling / topping / bottoming
3. Policy direction: easing / neutral / tightening / turning
4. Composite stage: recovery / overheat / stagflation / recession
5. Cycle position: early / mid / late
```

### Step 3: Policy Impact Assessment

```
1. Recent policy events (last 30 days)
2. Interpretation of policy intent (support growth / control inflation / contain risk)
3. Transmission paths to each asset class
4. Lag estimation (6-12 months for monetary policy, 3-6 months for fiscal policy)
```

### Step 4: Asset Allocation Tilt

```
Based on cycle position and policy direction:
- Overweight / neutral / underweight: China A-shares / Hong Kong stocks / US equities / bonds / commodities / cash
- Style tilt: growth vs value, large cap vs small cap
- Sector preference: cyclical / defensive / growth
```

## Output Format

```markdown
## Macro Environment Assessment

### Snapshot of Core Data
| Indicator | Latest | Previous | Trend |
|------|--------|------|------|
| China PMI | 50.2 | 49.8 | ↑ |
| ... | ... | ... | ... |

### Economic Cycle Positioning
- **Current stage**: early recovery / mid-overheat / late stagflation / mid-recession
- **Core logic**: explain the basis in 2-3 sentences
- **Estimated remaining duration**: expected to last another X months

### Central Bank Policy Analysis
- **PBOC**: easing bias, likely another 25bp RRR cut in Q2
- **Fed**: hiking pause, watch the June dot plot
- **Policy conflicts**: whether there are conflicting policy signals worth attention

### Major Asset Allocation Tilt
| Asset | Recommendation | Logic |
|------|------|------|
| China A-shares | Overweight | Policy bottom confirmed + loose liquidity |
| Bonds | Neutral | Limited room for rates to fall further |
| Commodities | Underweight | Weak demand |
| Cash | Underweight | High opportunity cost |

### Risk Warnings
- Risk 1: ...
- Risk 2: ...
```

## Notes

1. **Data timeliness**: macro data is released with lags; PMI is the timeliest (start of month), GDP is the most delayed (quarter-end + 15 days)
2. **Do not predict precisely**: macro analysis provides directional judgment, not exact levels or timing
3. **Focus on marginal change**: direction and speed of change matter more than absolute levels
4. **China-specific feature**: policy intent > economic data, and major meeting tone-setting has the highest priority
5. **Global linkage**: the US dollar / US Treasury yields are global pricing anchors, and Fed policy affects global liquidity
6. **Avoid hindsight bias**: analyze based on the information available at the time, not by reverse-engineering from future data
