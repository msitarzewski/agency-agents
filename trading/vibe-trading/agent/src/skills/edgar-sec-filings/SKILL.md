---
name: edgar-sec-filings
description: SEC EDGAR filing analysis — 10-K, 10-Q, 8-K, proxy statements, insider Form 4. Extract key financials, risk factors, management discussion, and generate investment signals from US public company filings.
category: flow
---
# SEC EDGAR Filing Analysis

## Overview

Analyze US public company filings from SEC EDGAR to extract fundamental insights, risk signals, and investment-relevant information. Covers annual reports (10-K), quarterly reports (10-Q), current events (8-K), proxy statements (DEF 14A), and insider transactions (Form 4).

This skill provides the analytical framework for interpreting SEC filings. Data retrieval uses `read_url` tool with EDGAR URLs or `yfinance` Ticker objects for structured financial data.

## Filing Types and Investment Relevance

| Filing | Frequency | Key Content | Signal Value |
|--------|-----------|-------------|--------------|
| 10-K | Annual | Full-year financials, risk factors, MD&A, segment data | Comprehensive fundamental view |
| 10-Q | Quarterly | Quarterly financials, interim MD&A, legal updates | Trend confirmation / inflection detection |
| 8-K | Event-driven | Material events: M&A, CEO change, restatement, guidance | Catalyst / risk trigger |
| DEF 14A | Annual (proxy) | Executive comp, board composition, shareholder proposals | Governance quality signal |
| Form 4 | Within 2 days | Insider buys / sells | Insider conviction signal |
| 13F | Quarterly | Institutional holdings >$100M AUM | Smart money positioning |
| SC 13D/G | Event-driven | >5% ownership stake disclosure | Activist / strategic investor signal |

## EDGAR Data Access

### Direct EDGAR URLs

```python
# Company filings search
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={filing_type}

# Example: Apple 10-K filings
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL&type=10-K&dateb=&owner=include&count=10"

# EDGAR full-text search (EFTS)
# https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}
```

### Via yfinance (structured data)

```python
import yfinance as yf
ticker = yf.Ticker("AAPL")

# Financial statements (derived from 10-K/10-Q)
income = ticker.financials           # Annual income statement
income_q = ticker.quarterly_financials  # Quarterly
balance = ticker.balance_sheet       # Balance sheet
cashflow = ticker.cashflow           # Cash flow statement

# Insider transactions (derived from Form 4)
insider = ticker.insider_transactions

# Institutional holders (derived from 13F)
institutions = ticker.institutional_holders
major = ticker.major_holders
```

## 10-K / 10-Q Analysis Framework

### I. Financial Statement Deep Dive

**Income Statement Focus:**
- Revenue growth rate: YoY and QoQ acceleration / deceleration
- Gross margin trend: expanding (pricing power) vs compressing (cost pressure)
- Operating leverage: SG&A as % of revenue declining = positive operating leverage
- R&D intensity: R&D / revenue ratio vs peers
- Non-recurring items: restructuring charges, impairments, one-time gains

**Balance Sheet Focus:**
- Cash & equivalents vs total debt: net cash / net debt position
- Current ratio and quick ratio: liquidity health
- Goodwill / intangibles as % of total assets: acquisition-driven growth risk
- Inventory days (for manufacturers / retailers): rising = demand weakness signal
- Accounts receivable days: rising = collection risk or channel stuffing

**Cash Flow Focus:**
- FCF = Operating CF - CapEx: true cash generation power
- FCF conversion = FCF / Net Income: >80% = high earnings quality
- CapEx intensity = CapEx / Revenue: rising = growth investment or maintenance burden
- Stock-based compensation: add back to get true cash earnings
- Buyback vs dividend: capital return strategy signal

### II. MD&A (Management Discussion & Analysis)

The MD&A section is the most qualitative and forward-looking part of the filing.

**Key extraction targets:**
1. **Revenue drivers**: which segments / geographies are growing, which are declining
2. **Margin commentary**: management explanation for margin changes
3. **Forward guidance language**: "expect", "anticipate", "believe" — tone shift detection
4. **Risk factor changes**: compare risk factors vs prior filing; NEW risks added = material change
5. **Liquidity and capital resources**: debt maturity schedule, credit facility availability

**Tone analysis signals:**
```python
# Simplified tone scoring
positive_words = ["growth", "improvement", "strong", "exceeded", "momentum", "opportunity"]
negative_words = ["challenging", "decline", "uncertainty", "headwind", "pressure", "risk"]
cautious_words = ["moderate", "cautious", "prudent", "measured", "selective"]

# Count frequency change vs prior filing
# Rising negative word count = deteriorating outlook
# Rising cautious words = management hedging
```

### III. Risk Factor Analysis

**Risk factor change detection (10-K vs prior 10-K):**

| Change Type | Signal | Action |
|-------------|--------|--------|
| New risk factor added | Material new risk identified | Deep dive on the specific risk |
| Risk factor removed | Risk resolved or deemed immaterial | Positive signal if genuine resolution |
| Language intensified | Risk escalating | Review exposure and hedging |
| Order changed (moved higher) | Risk priority elevated | Assess potential impact magnitude |

**Common risk categories for US equities:**
- Regulatory / legal risk (antitrust, FDA, patent expiry)
- Customer concentration (>10% revenue from single customer must be disclosed)
- Geographic concentration (China exposure, emerging market risk)
- Technology disruption risk
- Cybersecurity risk (new SEC mandate: material cybersecurity incidents must be disclosed in 8-K)
- Climate / ESG risk (increasingly required)

## 8-K Event Analysis

### Material Event Classification

| Event Type | 8-K Item | Typical Price Impact | Time Sensitivity |
|------------|----------|---------------------|------------------|
| Earnings pre-release | 2.02 | High | Immediate |
| M&A announcement | 1.01 | Very high | Immediate |
| CEO / CFO departure | 5.02 | Medium-high | Same day |
| Restatement | 4.02 | Very high (negative) | Immediate |
| Guidance revision | 7.01/8.01 | High | Same day |
| Credit agreement change | 1.01 | Low-medium | Monitor |
| Share repurchase program | 8.01 | Low positive | Background signal |
| Dividend change | 8.01 | Medium | Same day |

### 8-K Signal Rules

```python
# High-priority 8-K events
if item == "4.02":  # Restatement
    signal = "strong_negative"  # Restatements destroy trust
    action = "review_all_prior_financials"
elif item == "2.02" and surprise_direction == "negative":
    signal = "negative"  # Earnings pre-announcement miss
elif item == "5.02" and role in ["CEO", "CFO"]:
    signal = "uncertainty"  # C-suite departure = governance risk
elif item == "1.01" and event_type == "acquisition":
    signal = "evaluate"  # M&A: acquirer usually -2 to -5%, target +20-40%
```

## Insider Transaction Analysis (Form 4)

### Signal Framework

| Pattern | Signal | Confidence |
|---------|--------|------------|
| Cluster buying: 3+ insiders buying within 30 days | Strong bullish | High |
| CEO/CFO large open-market purchase (>$500K) | Bullish | High |
| Insider buying after price decline >20% | Contrarian bullish | Medium-high |
| Cluster selling at all-time highs | Neutral to mildly bearish | Low (may be pre-planned) |
| CFO selling >50% of holdings | Bearish | Medium |
| 10b5-1 plan sales | Neutral | Low (pre-programmed) |

**Key distinctions:**
- **Open-market purchases** (most informative): insider spending own money
- **10b5-1 plan sales** (least informative): pre-programmed, regulatory safe harbor
- **Option exercises + immediate sale**: often tax-driven, low signal value
- **Gift transactions**: ignore for signal purposes

```python
# Insider signal scoring
def score_insider_activity(transactions, lookback_days=90):
    buys = [t for t in transactions if t.type == "Purchase" and t.days_ago <= lookback_days]
    sells = [t for t in transactions if t.type == "Sale" and t.days_ago <= lookback_days]

    buy_value = sum(t.value for t in buys)
    sell_value = sum(t.value for t in sells)

    # Filter out 10b5-1 plan sales
    organic_sells = [s for s in sells if not s.is_10b5_1]

    if len(buys) >= 3 and buy_value > 1_000_000:
        return "strong_bullish"
    elif buy_value > sell_value * 2:
        return "bullish"
    elif len(organic_sells) >= 3 and sell_value > 5_000_000:
        return "bearish_watch"
    else:
        return "neutral"
```

## 13F Institutional Holdings Analysis

### Smart Money Tracking

**Key metrics:**
- Number of institutional holders: rising = broadening ownership base
- Top 10 holder concentration: >50% = concentrated, vulnerable to single-fund redemption
- New positions initiated this quarter: smart money entering
- Positions closed this quarter: smart money exiting
- Activist stakes (SC 13D): potential for corporate action catalyst

**Institutional quality tiers:**
1. **Tier 1 — Conviction signals**: Berkshire, Baupost, Greenlight, Pershing Square, Tiger Global
2. **Tier 2 — Trend signals**: BlackRock, Vanguard, Fidelity (flow-driven, less stock-picking signal)
3. **Tier 3 — Quantitative**: Renaissance, Two Sigma, Citadel (high turnover, less directional signal)

```python
# 13F change detection
def analyze_13f_changes(current_holders, prior_holders):
    new_positions = current_holders - prior_holders  # New entries
    closed_positions = prior_holders - current_holders  # Exits

    # Flag: multiple Tier 1 funds initiating
    tier1_new = [h for h in new_positions if h.tier == 1]
    if len(tier1_new) >= 2:
        signal = "strong_smart_money_accumulation"

    return signal
```

## Composite Filing Signal

### Scoring Template

```python
filing_score = {
    "financial_health": 0,       # -2 to +2: based on 10-K/10-Q financials
    "management_tone": 0,        # -2 to +2: MD&A sentiment shift
    "risk_factor_change": 0,     # -2 to +2: new risks vs resolved risks
    "insider_activity": 0,       # -2 to +2: net insider buying/selling
    "institutional_flow": 0,     # -2 to +2: 13F position changes
    "event_catalyst": 0,         # -2 to +2: recent 8-K impact
}
# Total range: -12 to +12
# > +6: strong fundamental bullish
# +2 to +6: mild bullish
# -2 to +2: neutral
# < -2: fundamental caution
```

## Output Format

```
## SEC Filing Analysis — [Ticker]

### Filing Summary
- **Latest 10-K/10-Q**: [date], [period]
- **Recent 8-K events**: [list material events]
- **Insider activity (90d)**: [net buy/sell summary]

### Financial Health
- Revenue trend: [accelerating / stable / decelerating]
- Margin trajectory: [expanding / stable / compressing]
- FCF conversion: [strong / adequate / weak]
- Balance sheet: [net cash / moderate leverage / high leverage]

### MD&A Tone Shift
- vs prior filing: [more optimistic / unchanged / more cautious]
- Key language changes: [specific quotes or paraphrases]

### Risk Factor Changes
- New risks: [list any new risk factors added]
- Intensified risks: [list risks with stronger language]
- Resolved risks: [list removed risk factors]

### Insider & Institutional Signals
- Insider net activity: [cluster buy / neutral / cluster sell]
- Institutional positioning: [accumulation / stable / distribution]

### Composite Signal
| Dimension | Score (-2~+2) | Basis |
|-----------|---------------|-------|
| Financial health | +1 | Revenue accelerating, margins stable |
| Management tone | -1 | More cautious language in MD&A |
| ... | ... | ... |

### Investment Implication
- Direction: [bullish / bearish / neutral]
- Confidence: [high / medium / low]
- Key monitoring: [next earnings date, upcoming 8-K triggers]
```

## Notes

- EDGAR filings are public and free; no API key required (rate limit: 10 requests/second with User-Agent header)
- 10-K/10-Q data is backward-looking; combine with forward guidance and analyst estimates for complete view
- Insider transaction data has a 2-business-day reporting lag; real-time insider data requires paid services
- 13F data is reported with a 45-day lag after quarter-end; positions may have already changed
- This framework is for research purposes only and does not constitute investment advice
