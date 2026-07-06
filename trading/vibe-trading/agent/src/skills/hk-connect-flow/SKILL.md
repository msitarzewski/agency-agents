---
name: hk-connect-flow
description: Stock Connect (Shanghai/Shenzhen-Hong Kong) fund flow analysis — Northbound (foreign into A-shares), Southbound (mainland into HK), sector allocation tracking, and cross-border arbitrage signals.
category: flow
---
# Stock Connect Fund Flow Analysis

## Overview

Analyze capital flows through the Shanghai-Hong Kong and Shenzhen-Hong Kong Stock Connect programs. Northbound flows (foreign capital into A-shares) are a key institutional sentiment indicator for the China market; Southbound flows (mainland capital into Hong Kong) reveal mainland investor preference for HK-listed assets. Together they provide a real-time cross-border capital positioning signal.

## Core Concepts

### 1. Stock Connect Architecture

| Channel | Direction | What It Measures |
|---------|-----------|------------------|
| Shanghai Connect Northbound | Foreign → A-shares (SSE) | Foreign institutional A-share appetite |
| Shenzhen Connect Northbound | Foreign → A-shares (SZSE) | Foreign institutional A-share appetite (growth bias) |
| Shanghai Connect Southbound | Mainland → HK (HKEX) | Mainland capital HK allocation |
| Shenzhen Connect Southbound | Mainland → HK (HKEX) | Mainland capital HK allocation |

**Daily quota**: Each channel has a daily net buy quota (~RMB 52B / HKD 42B). Quota utilization >50% = strong directional signal.

### 2. Northbound Flow Analysis (Foreign into A-shares)

**Why Northbound matters:**
- Foreign institutions (global funds, sovereign wealth funds, hedge funds) are considered "smart money" in A-shares
- Northbound holdings represent ~4-5% of A-share free-float market cap — small but marginal price-setters
- Northbound flow correlates with MSCI China index rebalancing and global EM allocation decisions

**Northbound signal framework:**

```python
# Daily Northbound net buy signals
def northbound_signal(daily_net_buy_rmb_billion):
    if daily_net_buy_rmb_billion > 10:
        return "strong_foreign_buying"    # Very large single-day inflow
    elif daily_net_buy_rmb_billion > 5:
        return "moderate_foreign_buying"
    elif daily_net_buy_rmb_billion > 0:
        return "mild_foreign_buying"
    elif daily_net_buy_rmb_billion > -5:
        return "mild_foreign_selling"
    elif daily_net_buy_rmb_billion > -10:
        return "moderate_foreign_selling"
    else:
        return "strong_foreign_selling"   # Panic outflow

# Cumulative flow trend (more important than single-day)
def northbound_trend(flows_20d, flows_5d):
    cum_20d = sum(flows_20d)
    cum_5d = sum(flows_5d)

    if cum_20d > 30 and cum_5d > 10:
        return "sustained_accumulation"   # Strong bullish for A-shares
    elif cum_20d < -30 and cum_5d < -10:
        return "sustained_distribution"   # Bearish for A-shares
    elif cum_20d > 0 and cum_5d < 0:
        return "accumulation_pausing"     # Watch for reversal
    elif cum_20d < 0 and cum_5d > 0:
        return "distribution_pausing"     # Possible bottom formation
```

**Northbound sector allocation patterns:**

| Sector Preference | Typical Holdings | Signal |
|-------------------|-----------------|--------|
| Consumer staples (Moutai, dairy) | 30-35% of holdings | Core allocation, low turnover |
| Financials (banks, insurance) | 15-20% | Cyclical allocation, rate-sensitive |
| Technology (semiconductors, software) | 10-15% | Growth allocation, high turnover |
| Healthcare (CXO, innovative pharma) | 8-12% | Structural growth bet |
| New energy (EV, solar) | 5-10% | Thematic, high volatility |

**Sector rotation signal:**
- When Northbound increases consumer staples weight → defensive positioning
- When Northbound increases tech/new energy weight → risk-on, growth chasing
- When Northbound reduces across all sectors → broad risk-off, usually FX-driven (CNY weakening)

### 3. Southbound Flow Analysis (Mainland into HK)

**Why Southbound matters:**
- Mainland investors are the marginal buyer for many HK mid/small caps
- Southbound flows are driven by: AH premium (A vs H discount arbitrage), dividend yield hunting, and tech platform allocation (Tencent, Alibaba, Meituan)
- Insurance and pension funds increasingly use Southbound for international diversification

**Southbound signal framework:**

```python
# Southbound focus areas
southbound_targets = {
    "tech_platforms": ["0700.HK", "9988.HK", "3690.HK", "9618.HK"],
    "high_dividend": ["0939.HK", "1398.HK", "0883.HK", "2628.HK"],
    "ah_discount": [],  # Dynamically calculated based on AH premium index
}

def southbound_signal(daily_net_buy_hkd_billion):
    if daily_net_buy_hkd_billion > 5:
        return "strong_mainland_buying"
    elif daily_net_buy_hkd_billion > 2:
        return "moderate_mainland_buying"
    elif daily_net_buy_hkd_billion < -2:
        return "mainland_selling"
    else:
        return "neutral"
```

**Southbound investment patterns:**
1. **Dividend yield arbitrage**: mainland funds buy HK-listed banks/telecoms for higher dividend yield (H-share dividends are often 2-3% higher than A-share equivalents due to lower prices)
2. **Tech platform allocation**: Tencent, Alibaba, Meituan are HK-only or HK-primary listings; mainland tech allocation must go Southbound
3. **AH premium arbitrage**: when AH premium index >130, arbitrage capital flows Southbound to buy cheaper H-shares

### 4. AH Premium Index

The Hang Seng AH Premium Index (HSAHP) tracks the average premium of A-shares over their H-share counterparts for dual-listed companies.

```python
# AH Premium interpretation
ah_premium_index = 130  # A-shares trade 30% above H-shares on average

if ah_premium_index > 140:
    signal = "extreme_ah_premium"
    action = "favor H-shares over A-shares for dual-listed names"
elif ah_premium_index > 125:
    signal = "elevated_ah_premium"
    action = "mild H-share preference"
elif ah_premium_index < 110:
    signal = "compressed_ah_premium"
    action = "A-shares relatively cheap vs H; unusual, investigate"
else:
    signal = "normal_range"
```

### 5. Cross-Border Flow Composite Signal

**Multi-dimensional scoring:**

```python
connect_score = {
    "northbound_flow": 0,       # -2 to +2: 20-day cumulative NB flow direction
    "northbound_breadth": 0,    # -2 to +2: number of NB top-10 holdings being added to
    "southbound_flow": 0,       # -2 to +2: 20-day cumulative SB flow direction
    "ah_premium": 0,            # -2 to +2: AH premium level (high = favor HK)
    "fx_direction": 0,          # -2 to +2: CNY strength (strong CNY = NB inflow support)
}

# Total range: -10 to +10
# > +5: strong cross-border risk-on, favor A-shares
# +2 to +5: mild bullish
# -2 to +2: neutral / mixed
# < -2: cross-border risk-off, foreign selling A-shares
# < -5: strong risk-off, likely FX-driven
```

## Data Access

### Via Tushare (A-share perspective)

```python
import tushare as ts
pro = ts.pro_api()

# Daily Northbound/Southbound aggregate flows
df = pro.moneyflow_hsgt(start_date="20260101", end_date="20260330")
# Columns: trade_date, ggt_ss (Shanghai SB), ggt_sz (Shenzhen SB),
#           hgt (Shanghai NB), sgt (Shenzhen NB), north_money, south_money

# Top 10 Northbound active stocks
df = pro.hsgt_top10(trade_date="20260328", market_type="1")  # 1=Shanghai, 3=Shenzhen
# Columns: trade_date, ts_code, name, close, change, rank, market_type,
#           amount (trade amount), net_amount (net buy), buy, sell
```

### Via yfinance (HK perspective)

```python
import yfinance as yf

# HK-listed stocks price data
tencent = yf.download("0700.HK", start="2025-01-01", end="2026-03-30", progress=False)
alibaba = yf.download("9988.HK", start="2025-01-01", end="2026-03-30", progress=False)

# AH Premium Index (proxy via Hang Seng indices)
hsi = yf.download("^HSI", start="2025-01-01", end="2026-03-30", progress=False)
```

### Key Data Points to Track

| Metric | Source | Frequency | Threshold |
|--------|--------|-----------|-----------|
| Northbound daily net buy | Tushare / HKEX | Daily | >RMB 5B = significant |
| Northbound 20-day cumulative | Calculated | Daily | >RMB 30B = trend |
| Southbound daily net buy | Tushare / HKEX | Daily | >HKD 3B = significant |
| AH Premium Index | Hang Seng | Daily | >130 = H-share value |
| Quota utilization | HKEX | Intraday | >50% = strong conviction |
| NB Top 10 concentration | Tushare | Daily | Top 3 names >50% = concentrated bet |

## Output Format

```
## Stock Connect Flow Analysis — [Date Range]

### Northbound (Foreign → A-shares)
- **20-day cumulative**: [+/- RMB X.XB]
- **5-day trend**: [accelerating / decelerating / reversing]
- **Daily average**: [RMB X.XB]
- **Quota utilization**: [X%]
- **Signal**: [sustained accumulation / distribution / neutral]

### Northbound Sector Allocation
- **Adding to**: [sector1 (top names), sector2]
- **Reducing**: [sector1, sector2]
- **Rotation direction**: [defensive / cyclical / growth]

### Southbound (Mainland → HK)
- **20-day cumulative**: [+/- HKD X.XB]
- **Focus names**: [Tencent, Alibaba, bank names]
- **Driver**: [dividend yield / tech allocation / AH arbitrage]

### AH Premium
- **Current index**: [XXX]
- **Historical percentile**: [X%]
- **Implication**: [favor H-shares / neutral / favor A-shares]

### Composite Signal
| Dimension | Score (-2~+2) | Basis |
|-----------|---------------|-------|
| NB flow | +1 | Cumulative +RMB 15B over 20 days |
| NB breadth | +2 | Adding across 8 of top 10 |
| SB flow | 0 | Flat |
| AH premium | -1 | AH premium at 135 (H relatively cheap) |
| FX | +1 | CNY stable/strengthening |

### Cross-Market Implication
- **A-share outlook**: [bullish / neutral / bearish] (NB perspective)
- **HK outlook**: [bullish / neutral / bearish] (SB + AH perspective)
- **Arbitrage**: [AH premium trade: buy H / sell A for dual-listed names]
```

## Notes

- Northbound flow is the single most-watched institutional indicator for A-shares; it often leads index turns by 1-3 days
- Quarter-end and MSCI rebalancing dates (Feb/May/Aug/Nov) cause mechanical flow distortions — filter these out for signal purity
- CNY/USD exchange rate is a key driver of Northbound flow; USD strength typically triggers NB outflows regardless of A-share fundamentals
- Southbound flow can be distorted by dividend arbitrage (mainland funds buy before ex-div, creating artificial inflow spikes)
- Stock Connect data is freely available from HKEX website and Tushare API
- This framework is for research purposes only and does not constitute investment advice
