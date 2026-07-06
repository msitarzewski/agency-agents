---
name: market-microstructure
description: "Market microstructure: bid-ask spread analysis, order-flow toxicity metrics (VPIN / Kyle lambda), liquidity measures (Amihud / Roll), price-impact models, limit-order-book analysis, and China A-share call auction / block trade mechanics."
category: analysis
---

# Market Microstructure

## Overview

Study the micro-level mechanisms of price formation: who is trading, how they are trading, and how trades affect prices. For quantitative strategies, this matters because it improves transaction-cost estimation, identifies informed trading, and optimizes execution.

Applicable scenarios:
- Precise estimation of strategy trading costs (instead of simply assuming a flat 0.1% fee)
- Designing large-order execution strategies (`TWAP / VWAP / IS`)
- Detecting order-flow toxicity (avoid time windows dominated by informed traders)
- Quantifying liquidity risk (flash-crash warning)
- Capturing China A-share-specific microstructure features (call auction / closing auction / block trades)

## Core Concepts

### Bid-Ask Spread

**Three measurements:**
| Metric | Formula | Meaning |
|------|------|------|
| Quoted spread | `Ask - Bid` | Best spread shown in the limit order book |
| Effective spread | `2 × |trade price - mid price|` | Actual spread paid by the trader |
| Realized spread | `2 × direction × (trade price - mid price 5min later)` | True market-maker profit |

```
China A-share example:
  Instrument: 600519.SH Kweichow Moutai
  Best bid: 1680.00  Best ask: 1680.50
  Quoted spread: 0.50 RMB = 0.03%

  Instrument: 000001.SZ Ping An Bank
  Best bid: 11.05  Best ask: 11.06
  Quoted spread: 0.01 RMB = 0.09%

Spread decomposition (Roll):
  Spread = adverse-selection cost + inventory cost + order-processing cost
  In China A-shares: adverse selection accounts for 60-70% (mixture of retail and informed traders)

Spread drivers:
  - Larger market cap -> smaller spread (Moutai 0.03% vs small-cap 0.5%)
  - Higher volatility -> wider spread (market-maker risk premium)
  - Higher volume -> narrower spread (greater competition)
  - Higher information asymmetry -> wider spread (adverse selection)
```

### Order-Flow Toxicity Metrics

**VPIN (Volume-Synchronized Probability of Informed Trading):**
```
Principle: replace clock time with volume time to measure the probability of informed trading

Calculation steps:
  1. Bucket trades by fixed volume (Volume Bucket)
     Bucket size V = average daily volume / 50 (about 5-10 minutes per bucket)

  2. Classify buy and sell volume in each bucket (Bulk Volume Classification):
     buy_volume = V × Φ(ΔP / σ)  (standard normal CDF)
     sell_volume = V - buy_volume

  3. Compute order-flow imbalance:
     OI_i = |buy_volume_i - sell_volume_i|

  4. VPIN = Σ(OI_i) / (n × V)  (n=50-bucket rolling window)

Interpretation:
  VPIN < 0.3 -> normal, low informed-trading share
  VPIN 0.3-0.5 -> caution, informed trading rising
  VPIN > 0.5 -> dangerous, high probability that major information is about to be released

China A-share usage:
  A sudden VPIN spike in a stock may foreshadow:
  - insider trading ahead of a major announcement
  - institutional position building / distribution
  Before the 2015 China A-share flash crashes, VPIN stayed above 0.6 for a prolonged period
```

**Kyle's Lambda (price impact coefficient)**:
```
Model: ΔP = λ × OrderFlow + ε
  where OrderFlow = buy volume - sell volume

Estimation method:
  1. Compute ΔP and OrderFlow in 5-minute windows
  2. Regress ΔP = α + λ × OrderFlow
  3. λ = price change caused by one unit of order flow

Interpretation:
  Large λ -> poor liquidity, high impact
  Small λ -> good liquidity, large orders can be executed cheaply

Typical China A-share values:
  Large cap (CSI 300): λ ≈ 0.001-0.005
  Mid cap (CSI 500): λ ≈ 0.005-0.02
  Small cap (CSI 1000): λ ≈ 0.02-0.1
```

### Liquidity Measures

| Metric | Formula | Advantages | Disadvantages |
|------|------|------|------|
| Amihud illiquidity | `|R_t| / Volume_t` | Requires only daily data | Sensitive to extreme returns |
| Roll implied spread | `2√(-Cov(R_t, R_{t-1}))` | Requires only daily data | Fails when covariance is positive |
| LOT zero-return ratio | zero-return days / total days | Intuitive | Too coarse |
| Turnover ratio | volume / free float | Simple and intuitive | Does not reflect price impact |
| Traded value | average daily notional | Absolute liquidity | Does not reflect relative impact |

```
Amihud calculation (China A-shares):
  ILLIQ = (1/D) × Σ(|R_d| / VOL_d)  (D=trading days, monthly)

  Normalization: ILLIQ × 10^6 (for readability)

  Screening rules:
    ILLIQ < 0.5 -> high liquidity (large-cap blue chips)
    ILLIQ 0.5-5 -> medium liquidity
    ILLIQ > 5 -> low liquidity (trade cautiously)

  Strategy application:
    - Liquidity factor: low-liquidity stocks tend to earn long-run excess return (liquidity premium)
    - Liquidity monitor: sudden rise in ILLIQ -> warning of liquidity drying up
```

## Analysis Framework

### 1. Price-Impact Models

**Linear impact (Almgren-Chriss)**:
```
Model: impact = η × σ × (Q / V)^0.6
  η: impact coefficient, about 0.5-1.5 for China A-shares
  σ: daily volatility
  Q: traded quantity (shares)
  V: average daily volume (shares)

Example:
  Sell 100,000 shares of Kweichow Moutai
  Average daily volume 5,000,000 shares, daily volatility 1.8%
  impact = 1.0 × 0.018 × (100000/5000000)^0.6
         = 0.018 × 0.0085
         = 0.015% (1.5bp, acceptable)

  Sell 100,000 shares of a small-cap stock
  Average daily volume 500,000 shares, daily volatility 3.0%
  impact = 1.0 × 0.03 × (100000/500000)^0.6
         = 0.03 × 0.076
         = 0.23% (23bp, should be executed in slices)

Execution-splitting methods:
  TWAP: uniform in clock time -> simple but ignores market state
  VWAP: volume-profile execution -> better matches market rhythm
  IS: minimize Implementation Shortfall -> optimal but requires real-time optimization
```

**Nonlinear impact (square-root model)**:
```
impact = σ × √(Q / (ADV × T))
  σ: daily volatility
  Q: total trade size
  ADV: average daily traded value
  T: execution days

Applicable to: large trades (Q/ADV > 5%)
```

### 2. Limit Order Book Analysis

```
Depth metrics:
  Level 1 depth: queue size at the best bid and best ask
  Level 5 depth: total queue size across the first 5 levels
  Depth asymmetry: (Bid depth - Ask depth) / (Bid depth + Ask depth)
    > 0 -> stronger bid side, price tends to rise
    < 0 -> stronger ask side, price tends to fall

Resilience:
  The speed at which the book recovers after a large-order impact
  Fast recovery -> good liquidity, temporary impact
  Slow recovery -> poor liquidity, persistent impact

China A-share LOB characteristics:
  - The shallowest depth is in the 15 minutes before the open (highest information asymmetry)
  - Depth improves from 10:00-10:30 (institutions begin participating)
  - Best depth is from 14:00-14:57 (most intraday information has been digested)
  - During the 14:57-15:00 closing auction, depth changes sharply (late-day grabbing / dumping)

Order-book imbalance signal:
  OIR = (Bid_vol - Ask_vol) / (Bid_vol + Ask_vol)
  Rolling 5-minute OIR > 0.3 -> short-term bullish signal (accuracy about 55-60%)
  Note: in China A-shares, large orders are often rapidly added and canceled (icebergs / spoofing), so OIR signals need filtering
```

### 3. Flash-Crash Mechanism and Prevention

```
Flash-crash characteristics:
  1. Price drops more than 5% within minutes
  2. Volume first expands, then collapses (liquidity evaporates)
  3. Bid-ask spread widens sharply (market makers pull quotes)
  4. Followed by a V-shaped rebound (not always fully recovered)

Triggers:
  - Large market order + thin liquidity -> punches through multiple levels instantly
  - Stop-loss chain -> initial selloff triggers more stop orders
  - Algo resonance -> multiple trend-following algos sell simultaneously
  - ETF discount arbitrage -> ETF redemption and constituent selling intensify the drop

Preventive measures:
  1. Use limit orders instead of market orders: specify the maximum acceptable price
  2. Monitor VPIN: if VPIN breaks above 0.5 -> stop trading
  3. Liquidity threshold: exclude instruments with Amihud > 10
  4. Spread monitor: if spread widens suddenly to >5x normal -> pause orders
  5. Time avoidance: do not execute large orders in the first 15 minutes after open or the last 5 minutes before close

China A-share flash-crash cases:
  2015 Jun-Jul: thousands of stocks hit limit-down, with VPIN staying elevated
  2020-07-13: Shanghai Composite plunged and then rebounded in a V-shape
  Pattern: liquidity dries up -> limit-down locking (China-specific) -> next-day panic selling
```

### 4. China A-Share-Specific Microstructure

```
Call-auction strategy:
  9:15-9:20: orders can be entered and canceled, mostly probing quotes (low reference value)
  9:20-9:25: orders can be entered but not canceled, so real intent is revealed
  Signal: after 9:20, buy orders far exceed sell orders -> likely gap-up open

  Execution: place orders at 9:24:50 (last 10 seconds of the call auction)
  Risk: cannot cancel, and the final execution price may deviate from expectation

Closing call auction (14:57-15:00):
  Feature: closing price is decided within 3 minutes, with concentrated institutional rebalancing and index-fund flows
  Signal: closing-auction volume > 10% of the whole day -> institutions are rebalancing

  Strategy application:
  - VWAP algos should finish most of execution before 14:50, leaving a small residual for the close
  - Avoid placing large orders after 14:57 (high price uncertainty)

Block-trade discount signal:
  Discount = (block-trade price - closing price) / closing price
  Discount < -5%: seller is eager to exit -> short-term bearish
  Discount > -2%: traded near market price -> may be turnover rather than reduction

  Buyer identity:
  Well-known institutional seat buys -> positive signal
  Same broker on both sides -> may be wash trading (neutral)
```

## Output Format

Microstructure analysis report:
```
=== Liquidity Diagnosis ===
Instrument: 000858.SZ Wuliangye
Date: 2026-03-28
Average daily traded value: 2.8 billion RMB  Turnover ratio: 0.85%
Amihud: 0.32 (high liquidity)
Effective spread: 0.05% (2.5bp)
Kyle Lambda: 0.003

=== Order-Flow Analysis ===
VPIN: 0.28 (normal)
Order-book imbalance (OIR): +0.12 (mild bid-side bias)
Net large-order buying: +230 million RMB (institutional buying bias)

=== Trading-Cost Estimate ===
Planned trade size: 500,000 shares (about 40 million RMB)
Estimated impact cost: 0.08% (32k RMB)
Commission: 0.025% (10k RMB)
Stamp duty: 0.05% (20k RMB, sell side)
Total one-way transaction cost: about 0.16%

=== Execution Suggestion ===
Recommended strategy: VWAP
Execution window: 10:00-14:50 (avoid the open and the close)
Number of slices: 5-8 (about 60k-100k shares per slice)
Time sensitivity: low (VPIN is normal, no urgency to execute)
```

## Notes

1. **Data requirement is high**: microstructure analysis requires tick-level / Level-2 data, while ordinary daily data only supports rough measures such as Amihud / Roll
2. **China A-share Level-2 data**: ten-level depth data from SSE / SZSE requires a paid subscription, costing roughly 50k-200k RMB per year
3. **High-frequency trading restrictions**: China A-shares strictly prohibit programmatic quote-cancel manipulation (`spoofing`), so microstructure signals are for analysis only, not for HFT strategies
4. **VPIN calibration**: bucket size has a large impact on results and must be adjusted for instrument liquidity; one parameter does not fit all
5. **Cross-market differences**: China A-share `T+1` settlement and daily price limits make its microstructure significantly different from textbook US-equity models
6. **Illusion of liquidity**: high turnover in some China A-shares comes from speculative matched trading and does not represent true liquidity

## Dependencies

```bash
pip install pandas numpy scipy
```
