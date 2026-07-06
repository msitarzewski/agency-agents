---
name: earnings-revision
description: Earnings estimate revisions, guidance analysis, and post-earnings drift (PEAD) — track analyst consensus changes, earnings surprise patterns, and management guidance shifts for US/HK equities.
category: analysis
---
# Earnings Revision & Guidance Analysis

## Overview

Track sell-side analyst estimate revisions, management guidance changes, and post-earnings price drift to generate investment signals. Earnings revisions are among the most persistent and well-documented alpha factors in equity markets — stocks with upward revisions tend to continue outperforming, and vice versa.

## Core Concepts

### 1. Earnings Revision Momentum

**The revision signal hierarchy (strongest to weakest):**

| Signal Type | Description | Typical Alpha (annualized) | Persistence |
|-------------|-------------|---------------------------|-------------|
| Earnings surprise (beat/miss) | Actual EPS vs consensus | 3-8% post-event drift | 60-90 days (PEAD) |
| Consensus revision breadth | % of analysts revising up vs down | 4-6% long-short spread | 3-6 months |
| Estimate magnitude change | Size of revision relative to prior estimate | 3-5% | 1-3 months |
| Guidance revision | Management guidance change vs prior | 5-10% on event | Immediate + 30-60 day drift |
| Whisper number miss/beat | Actual vs buy-side whisper (not official consensus) | 2-4% | 1-2 weeks |

### 2. Key Metrics

**Earnings Surprise:**
```python
# Standardized Unexpected Earnings (SUE)
sue = (actual_eps - consensus_eps) / std_of_forecast_errors

# Interpretation
# SUE > +2: large positive surprise → strong PEAD signal
# SUE < -2: large negative surprise → strong negative PEAD
# |SUE| < 0.5: in-line with expectations → weak signal
```

**Revision Breadth:**
```python
# Revision breadth ratio
breadth = (num_upgrades - num_downgrades) / total_analysts

# Interpretation
# breadth > +0.5: strong consensus upgrade momentum
# breadth < -0.5: strong consensus downgrade momentum
# |breadth| < 0.2: mixed / no clear direction
```

**Estimate Dispersion:**
```python
# Analyst disagreement
dispersion = std_of_estimates / abs(mean_estimate)

# High dispersion (>15%): high uncertainty → larger potential surprise
# Low dispersion (<5%): tight consensus → smaller surprise but higher confidence
```

### 3. Post-Earnings Announcement Drift (PEAD)

The most robust anomaly in equity markets: prices continue to drift in the direction of the earnings surprise for 60-90 days after the announcement.

**PEAD trading rules:**

| Surprise Quintile | Average 60-day Drift | Strategy |
|-------------------|---------------------|----------|
| Q5 (top surprise) | +4 to +8% | Go long, hold 60-90 days |
| Q4 | +1 to +3% | Mild long |
| Q3 (in-line) | ~0% | No action |
| Q2 | -1 to -3% | Mild short / underweight |
| Q1 (worst surprise) | -4 to -8% | Go short / avoid, hold 60-90 days |

**PEAD enhancement filters:**
- Small/mid cap > large cap (less analyst coverage = slower price discovery)
- Low institutional ownership > high ownership (slower information diffusion)
- First surprise in a direction > consecutive same-direction surprises
- Revenue surprise + EPS surprise together > EPS surprise alone

### 4. Management Guidance Analysis

**Guidance types:**

| Type | What It Covers | Signal Weight |
|------|----------------|---------------|
| Revenue guidance | Top-line outlook | High (harder to manipulate) |
| EPS guidance | Bottom-line outlook | Medium (can be managed via buybacks, tax rate) |
| Margin guidance | Profitability trajectory | High (reflects pricing power and cost control) |
| CapEx guidance | Investment intentions | Medium (forward-looking growth signal) |
| Segment guidance | Division-level detail | High (reveals where growth is coming from) |

**Guidance change signals:**

```python
# Guidance revision scoring
def score_guidance_change(current_guide, prior_guide, consensus):
    # Guide above consensus = positive signal
    if current_guide.midpoint > consensus * 1.02:
        guide_vs_consensus = "above"
    elif current_guide.midpoint < consensus * 0.98:
        guide_vs_consensus = "below"
    else:
        guide_vs_consensus = "inline"

    # Guide raised vs lowered vs maintained
    if prior_guide:
        if current_guide.midpoint > prior_guide.midpoint * 1.01:
            guide_revision = "raised"
        elif current_guide.midpoint < prior_guide.midpoint * 0.99:
            guide_revision = "lowered"
        else:
            guide_revision = "maintained"

    # Strongest signal: raised guidance above consensus
    # Weakest signal: lowered guidance below consensus
```

**Guidance language analysis:**

| Language Pattern | Interpretation | Signal |
|-----------------|----------------|--------|
| "Raising full-year outlook" | Confidence in acceleration | Strong positive |
| "Reaffirming guidance" | No change, on-track | Mild positive (met expectations) |
| "Narrowing guidance range to upper half" | Soft raise without formal revision | Positive |
| "Updating guidance to reflect..." | Euphemism for guidance cut | Negative |
| "Withdrawing guidance" | High uncertainty, loss of visibility | Strong negative |
| "Providing preliminary results" | Pre-announcement, usually bad news | Negative (if below consensus) |

### 5. Earnings Quality Indicators

**Red flags in earnings reports:**
1. Revenue growing but cash flow declining → accrual manipulation
2. Changing revenue recognition policy → inflating top line
3. Declining DSO (Days Sales Outstanding) story contradicted by rising AR → channel stuffing
4. Beating EPS via lower tax rate or share buyback, not operating improvement
5. Frequent "non-GAAP adjustments" that always add back expenses → questionable earnings quality
6. Inventory build outpacing revenue growth → future write-down risk

**Quality scoring:**
```python
earnings_quality = {
    "fcf_conversion": fcf / net_income,           # >0.8 = good, <0.5 = poor
    "accrual_ratio": (net_income - ocf) / avg_assets,  # <5% = good, >10% = concern
    "revenue_cash_alignment": revenue_growth - ocf_growth,  # small gap = good
    "non_gaap_gap": non_gaap_eps - gaap_eps,      # large gap = red flag
    "buyback_eps_boost": eps_growth - net_income_growth,  # large = artificial
}
```

## Earnings Calendar and Workflow

### Pre-Earnings Analysis Checklist

1. **Consensus snapshot**: current EPS/revenue consensus, revision trend (30d/60d/90d)
2. **Historical surprise pattern**: has the company consistently beat/missed? By how much?
3. **Guidance comparison**: last quarter's guidance vs current consensus
4. **Whisper number**: buy-side expectations (often 1-3% above street consensus for serial beaters)
5. **Options market pricing**: implied move from at-the-money straddle
6. **Sector peers already reported**: read-through signals from competitors

### Post-Earnings Analysis Checklist

1. **Headline numbers**: EPS surprise %, revenue surprise %
2. **Quality of beat/miss**: operating income-driven or one-time items?
3. **Guidance change**: raised / maintained / lowered / withdrawn
4. **Call tone**: management confidence level, Q&A defensiveness
5. **Analyst reaction**: immediate revision direction (first 24-48 hours)
6. **Price/volume reaction**: gap up/down, reversal, volume multiple vs average

## Multi-Market Considerations

### US Equities
- Earnings season: Jan/Apr/Jul/Oct (roughly 2-6 weeks after quarter-end)
- Data: SEC filings (10-Q within 40 days, 10-K within 60 days for large accelerated filers)
- Consensus: Bloomberg, Refinitiv, FactSet, Visible Alpha
- Via yfinance: `ticker.earnings_dates`, `ticker.earnings_history`

### Hong Kong Equities
- Earnings season: Mar-Apr (annual), Aug-Sep (interim)
- Many HK-listed companies report semi-annually, not quarterly
- Dual-listed (A+H): compare A-share analyst estimates vs HK analyst estimates for arbitrage
- Via yfinance: `yf.Ticker("0700.HK").financials`

### Key Differences

| Dimension | US | HK |
|-----------|----|----|
| Reporting frequency | Quarterly | Semi-annual (most) |
| Guidance practice | Common | Rare |
| Analyst coverage | Deep (>20 for large caps) | Thinner (5-15 for large caps) |
| Pre-announcement | Regulated (Reg FD) | Less regulated |
| Earnings call | Standard | Less common for mid/small caps |

## Output Format

```
## Earnings Revision Analysis — [Ticker]

### Consensus Snapshot
- **Current FY EPS consensus**: $X.XX (N analysts)
- **30-day revision**: [up/down X%] — [N upgrades / N downgrades]
- **60-day revision**: [up/down X%]
- **Estimate dispersion**: [low/medium/high] (CV = X%)

### Last Earnings Event
- **Date**: YYYY-MM-DD | **Quarter**: FY25Q3
- **EPS**: $X.XX actual vs $X.XX consensus (surprise: +X%)
- **Revenue**: $X.XB actual vs $X.XB consensus (surprise: +X%)
- **Guidance**: [raised / maintained / lowered] — FY25 EPS guide: $X.XX-$X.XX
- **Price reaction**: [+X% on day, +X% over 5 days]

### Revision Momentum
- **Breadth**: [+0.6 → strong upgrade momentum]
- **Magnitude**: [average revision +X% over 30 days]
- **PEAD status**: [still within 60-day drift window / drift exhausted]

### Earnings Quality
- **FCF conversion**: X% [strong/adequate/weak]
- **Accrual ratio**: X% [clean/moderate/concern]
- **Non-GAAP gap**: $X.XX [small/large]

### Signal
- **Direction**: [bullish / neutral / bearish]
- **Catalyst**: [next earnings date: YYYY-MM-DD]
- **Confidence**: [high / medium / low]
```

## Notes

- Earnings revision data requires real-time consensus feeds (Bloomberg, Refinitiv) for professional-grade signals; yfinance provides historical actuals but not real-time consensus
- PEAD is strongest in the first 30 days post-announcement; signal decays significantly after 60 days
- Guidance withdrawals are almost always negative — companies rarely withdraw guidance when business is going well
- Beware of "beat and lower" — beating current quarter but lowering forward guidance is often net negative
- This framework is for research purposes only and does not constitute investment advice
