---
name: us-etf-flow
description: US ETF fund flow analysis, sector rotation breadth, and style factor flows — track institutional capital movement via ETF creation/redemption, sector breadth signals, and thematic momentum.
category: flow
---
# US ETF Flow & Sector Breadth Analysis

## Overview

Track capital flows through US ETFs to identify institutional positioning, sector rotation trends, and risk appetite shifts. ETF flows are a real-time proxy for institutional capital allocation — unlike 13F filings (45-day lag), ETF creation/redemption data is available daily.

## Core Concepts

### 1. ETF Flow Mechanics

**Creation / Redemption process:**
- **Inflows (creation)**: Authorized Participants (APs) deliver baskets of underlying securities to the ETF issuer → receive new ETF shares → sell on exchange. This happens when ETF trades at a premium to NAV.
- **Outflows (redemption)**: APs buy ETF shares on exchange → redeem with issuer for underlying securities → sell securities. This happens when ETF trades at a discount to NAV.
- **Signal interpretation**: sustained large inflows = institutional demand; sustained large outflows = institutional liquidation.

**Key distinction:**
- ETF price movement ≠ ETF flow. Price can rise on low volume (momentum). Flows require actual capital commitment.
- Flows are a **quantity** signal (how much money is moving), not a **price** signal.

### 2. Major ETF Flow Categories

#### Broad Market ETFs

| ETF | Tracking Index | AUM | Flow Signal |
|-----|---------------|-----|-------------|
| SPY | S&P 500 | ~$500B | Broadest equity risk appetite |
| IVV | S&P 500 | ~$400B | Long-term institutional allocation |
| VOO | S&P 500 | ~$400B | Retail + advisor allocation |
| QQQ | Nasdaq 100 | ~$250B | Tech / growth appetite |
| IWM | Russell 2000 | ~$60B | Small-cap risk appetite |
| DIA | Dow Jones 30 | ~$30B | Value / blue-chip sentiment |

**Interpretation rules:**
```python
# Broad market flow signals
if spy_flow > 0 and iwm_flow > 0:
    signal = "risk_on"  # Both large and small cap getting inflows
elif spy_flow > 0 and iwm_flow < 0:
    signal = "quality_flight"  # Money rotating to large-cap safety
elif spy_flow < 0 and iwm_flow < 0:
    signal = "risk_off"  # Broad equity outflows
elif spy_flow < 0 and iwm_flow > 0:
    signal = "risk_seeking"  # Rotation from large to small (rare, usually early cycle)
```

#### Sector ETFs (SPDR Select Sector)

| ETF | Sector | Economic Sensitivity | Cycle Phase |
|-----|--------|---------------------|-------------|
| XLK | Technology | Growth / late cycle | Expansion |
| XLF | Financials | Rate sensitive | Early recovery |
| XLE | Energy | Commodity linked | Late cycle / inflation |
| XLV | Healthcare | Defensive | Recession |
| XLY | Consumer Discretionary | Cyclical | Recovery |
| XLP | Consumer Staples | Defensive | Recession |
| XLI | Industrials | Cyclical | Early expansion |
| XLU | Utilities | Defensive / rate sensitive | Late cycle / recession |
| XLB | Materials | Commodity linked | Early cycle |
| XLRE | Real Estate | Rate sensitive | Rate-cut cycle |
| XLC | Communication Services | Growth (META, GOOGL) | Expansion |

#### Style & Factor ETFs

| ETF | Factor | Signal |
|-----|--------|--------|
| IVW / SPYG | S&P 500 Growth | Growth appetite |
| IVE / SPYV | S&P 500 Value | Value rotation |
| MTUM | MSCI USA Momentum | Trend following |
| QUAL | MSCI USA Quality | Quality flight |
| USMV / SPLV | Min Volatility | Defensive positioning |
| SIZE | MSCI USA Size | Small-cap factor |

#### Fixed Income ETFs

| ETF | Segment | Signal |
|-----|---------|--------|
| TLT | 20+ Year Treasury | Duration / rate expectations |
| IEF | 7-10 Year Treasury | Intermediate rate view |
| SHY | 1-3 Year Treasury | Cash proxy / safe haven |
| LQD | Investment Grade Corp | Credit appetite |
| HYG / JNK | High Yield Corp | Risk appetite / credit cycle |
| TIP | TIPS | Inflation expectations |
| EMB | EM Sovereign Debt | EM risk appetite |

### 3. Sector Rotation Signals

**Sector breadth analysis:**
```python
# Sector breadth = number of sectors with positive flows / total sectors
sector_flows = {
    "XLK": +500,  # $500M inflow
    "XLF": +200,
    "XLE": -100,
    "XLV": +50,
    "XLY": -300,
    "XLP": +100,
    "XLI": +150,
    "XLU": -50,
    "XLB": +80,
    "XLRE": -200,
    "XLC": +300,
}

positive_sectors = sum(1 for v in sector_flows.values() if v > 0)
breadth = positive_sectors / len(sector_flows)

# Interpretation
# breadth > 0.7: broad-based inflows → healthy bull market
# breadth 0.4-0.7: selective rotation → stock/sector picker's market
# breadth < 0.4: broad outflows → risk-off environment
```

**Cyclical vs Defensive ratio:**
```python
cyclical = ["XLK", "XLY", "XLI", "XLF", "XLB"]
defensive = ["XLV", "XLP", "XLU", "XLRE"]

cyclical_flow = sum(sector_flows[s] for s in cyclical)
defensive_flow = sum(sector_flows[s] for s in defensive)

ratio = cyclical_flow / (cyclical_flow + defensive_flow + 1e-10)

# ratio > 0.65: strong risk-on, cyclical leadership
# ratio 0.4-0.65: balanced
# ratio < 0.4: defensive rotation, risk-off
```

### 4. Thematic ETF Flows

**Growth / innovation themes:**

| Theme | Key ETFs | What It Tracks |
|-------|----------|---------------|
| AI / Semiconductors | SMH, SOXX, BOTZ | AI capex cycle |
| Clean Energy | ICLN, TAN, QCLN | Energy transition spend |
| Biotech | XBI, IBB | Pharma pipeline / M&A cycle |
| Cybersecurity | CIBR, HACK | Security spending cycle |
| China Internet | KWEB, FXI | China tech sentiment |
| India | INDA, SMIN | India growth allocation |
| Emerging Markets | EEM, VWO | EM risk appetite |
| Gold Miners | GDX, GDXJ | Gold price leverage play |
| Bitcoin | IBIT, FBTC | Crypto institutional adoption |

**Thematic flow interpretation:**
- Sustained 4-week+ inflows into a theme = institutional conviction, not just hot money
- Sudden large outflows from a theme that was trending = crowded trade unwind risk
- Divergence between thematic ETF flow and underlying asset price = potential inflection

### 5. Flow-Based Trading Signals

**Signal construction:**

```python
def etf_flow_signal(ticker, lookback_days=20):
    """
    Generate trading signal from ETF flow data.
    """
    # Cumulative flow over lookback period
    cum_flow = sum(daily_flows[ticker][-lookback_days:])

    # Flow as % of AUM (normalized)
    flow_pct = cum_flow / aum[ticker]

    # Flow momentum: recent 5-day vs prior 15-day
    recent = sum(daily_flows[ticker][-5:])
    prior = sum(daily_flows[ticker][-20:-5])
    momentum = recent - prior

    # Signal
    if flow_pct > 0.02 and momentum > 0:
        return "strong_inflow"   # Sustained and accelerating
    elif flow_pct > 0.01:
        return "mild_inflow"     # Positive but not accelerating
    elif flow_pct < -0.02 and momentum < 0:
        return "strong_outflow"  # Sustained and accelerating outflows
    elif flow_pct < -0.01:
        return "mild_outflow"
    else:
        return "neutral"
```

**Contrarian vs momentum flow signals:**
- **Momentum** (follow the flow): works best for broad market ETFs (SPY, QQQ) during trending markets
- **Contrarian** (fade extreme flows): works best for sector/thematic ETFs at extreme levels
- **Rule of thumb**: 3-standard-deviation flow events in sector ETFs tend to mean-revert within 2-4 weeks

## Data Access

### Via yfinance

```python
import yfinance as yf

# ETF price and volume data
etf = yf.download("SPY", start="2025-01-01", end="2026-03-30", progress=False)

# ETF info (AUM, expense ratio, holdings)
spy = yf.Ticker("SPY")
info = spy.info
print(f"AUM: {info.get('totalAssets')}")
print(f"Expense ratio: {info.get('annualReportExpenseRatio')}")

# Sector weights (for sector ETFs)
# Not directly available via yfinance; use web scraping or manual input
```

### Flow Data Sources

| Source | Access | Coverage | Latency |
|--------|--------|----------|---------|
| ETF.com | Free (web) | US ETFs | T+1 |
| Bloomberg Terminal | Paid | Global ETFs | Real-time |
| ICI (Investment Company Institute) | Free (weekly) | US mutual fund + ETF aggregate | T+7 |
| ETF Database (etfdb.com) | Free (web) | US ETFs | T+1 |
| VettaFi | Free (web) | US ETFs | T+1 |

## Output Format

```
## ETF Flow Analysis — [Date Range]

### Broad Market Flows
- **SPY**: [+/- $X.XB over N days] — [risk-on / risk-off signal]
- **QQQ**: [+/- $X.XB] — [tech appetite]
- **IWM**: [+/- $X.XB] — [small-cap sentiment]
- **Overall**: [risk-on / selective / risk-off]

### Sector Rotation
- **Inflow leaders**: [sector1 +$XM, sector2 +$XM]
- **Outflow leaders**: [sector1 -$XM, sector2 -$XM]
- **Breadth**: X/11 sectors with positive flows
- **Cyclical/Defensive ratio**: X.XX [risk-on / balanced / defensive]

### Style Factor Flows
- **Growth vs Value**: [growth leading / value leading / balanced]
- **Momentum**: [inflow / outflow]
- **Quality/MinVol**: [inflow = defensive, outflow = risk-on]

### Fixed Income Flows
- **Duration signal**: TLT [inflow/outflow] → [rate cut expectations / rate concern]
- **Credit signal**: HYG [inflow/outflow] → [credit cycle expansion / contraction]
- **Inflation signal**: TIP [inflow/outflow] → [rising / falling inflation expectations]

### Thematic Highlights
- [Theme1 ETF]: [flow trend and implication]
- [Theme2 ETF]: [flow trend and implication]

### Composite Signal
| Dimension | Signal | Basis |
|-----------|--------|-------|
| Risk appetite | [on/off] | SPY+QQQ flows, C/D ratio |
| Sector rotation | [early/mid/late cycle] | Sector flow pattern |
| Rate expectations | [cuts/hold/hikes] | TLT + TIP flows |

### Investment Implication
- **Positioning**: [overweight equities / neutral / underweight]
- **Sector tilts**: [overweight X, underweight Y]
- **Risk level**: [high / moderate / low]
```

## Notes

- ETF flows are a proxy for institutional behavior, not a standalone signal; combine with price action and fundamentals
- Large single-day flows can be rebalancing-driven (quarter-end, index reconstitution) rather than directional
- Options-related ETF activity (hedging via SPY puts) can distort flow signals
- International ETF flows (EEM, FXI, INDA) are useful for global macro positioning
- This framework is for research purposes only and does not constitute investment advice
