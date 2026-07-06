---
name: behavioral-finance
description: "Behavioral finance applications: theories of overreaction and underreaction, behavioral explanations for momentum and reversal, investor sentiment cycles, cognitive-bias checklists, and debiasing quantitative strategies."
category: analysis
---

# Behavioral Finance Applications

## Overview

Translate behavioral-finance theory into quantifiable trading signals and risk-control rules. Core assumption: market participants systematically deviate from rational decision-making, and these biases can be predicted and exploited.

Applicable scenarios:
- Behavioral interpretation and parameter optimization for momentum / reversal strategies
- Contrarian signals when market sentiment becomes extreme
- Debiasing mechanisms in portfolio construction
- Capturing behavior patterns specific to retail-driven China A-share markets

## Core Concepts

### Overreaction and Underreaction

**Underreaction** → momentum effect:
```
Mechanism: anchoring bias + conservatism
  Investors anchor on old information and update insufficiently to new information
  After an earnings beat, the stock price digests it gradually rather than all at once
China A-share evidence:
  - Earnings-guidance beats still produce 3-5% excess return over the following 20 days
  - After analyst rating upgrades, momentum often persists for 1-3 months
Quant signal:
  SUE (standardized unexpected earnings) > 2σ -> buy and hold for 60 days
  Top 10% 20-day return -> continue holding for 20 days (China A-share momentum cycles are shorter)
```

**Overreaction** → reversal effect:
```
Mechanism: representativeness heuristic + availability bias
  Investors extrapolate recent trends too aggressively and ignore mean reversion
  Panic / euphoria drives reactions beyond what fundamentals support
China A-share evidence:
  - Rebounds after consecutive limit-downs (after 3 limit-downs, the average 20-day rebound is 8%)
  - Big annual losers often earn 5-10% excess return the next year
Quant signal:
  Bottom 10% of 250-day return -> buy and hold for 250 days
  RSI(5) < 10 -> short-term rebound signal (5-10 days)
```

**Key distinction**:
| Dimension | Underreaction (Momentum) | Overreaction (Reversal) |
|------|------------------|------------------|
| Time scale | 1-12 months | <1 week or >12 months |
| Information type | Clear events (earnings / announcements) | Ambiguous information (sentiment / trend) |
| Best China A-share window | 20-60 days | 5-10 days (short term) / 1 year (long term) |

### Cognitive Bias Checklist

**Individual decision biases**:
| Bias | Manifestation | Quant Detection | Debiasing Strategy |
|------|------|----------|------------|
| Loss aversion | Hold losing stocks, sell winners too early | Holding period: losing positions > winning positions by 2-3x | Pre-set stop-loss line and execute mechanically |
| Overconfidence | Overtrading, concentrated positions | Monthly turnover > 100%, single-stock weight > 30% | Limit the number of trades per month |
| Anchoring effect | Anchoring to entry price / historical highs | Abnormal volume expansion near the entry price | Use relative valuation instead of absolute price |
| Confirmation bias | Focus only on information that supports the existing view | Single-source information, ignoring bearish news | Force reading the opposing view |
| Recency bias | Overweight recent events | Recent gains/losses have too much influence on position size | Lengthen the evaluation window (≥60 days) |
| Framing effect | Same information framed differently leads to different decisions | Decision differences between return format and absolute-PnL format | Evaluate consistently in return space |

**Group behavior biases**:
| Bias | Manifestation | China A-share Characteristics | Quant Indicator |
|------|------|---------|----------|
| Herding | Chasing rallies and panic-selling together | Extremely fast sector rotation (3-5 days) | Intra-sector stock correlation > 0.8 |
| Information cascades | Ignoring private information and following public signals | Sector follow-through after a leader stock hits limit-up | Sector return on the day after leader-stock limit-up |
| Attention effect | Buying stocks that attract attention | Explosive turnover in limit-up / news-driven stocks | Abnormal turnover > 3x average |

### Investor Sentiment Cycle

```
Fear -> Caution -> Optimism -> Excitement -> Euphoria -> Denial -> Panic -> Fear
  |        |        |        |        |       |        |
 Bottom   Recovery  Mid-uptrend  Pre-top   Top   Early selloff  Pre-bottom

Quant sentiment indicators:
  1. Closed-end fund discount: discount > 15% -> extreme fear -> buy signal
  2. Margin-financing growth: monthly growth > 20% -> euphoria -> reduce position
  3. New account openings: weekly openings > 2x average -> overheated market
  4. Turnover ratio: All-A daily turnover > 3% -> euphoric; < 0.5% -> deeply depressed
  5. Number of limit-up stocks: > 100 -> euphoric; < 10 -> weak
```

## Analysis Framework

### 1. Disposition-Effect Signal

**Principle**: investors tend to sell winners and hold losers. Once winning positions are largely cleared, selling pressure eases; when trapped holders are deeply underwater, selling pressure can also ease.

```
China A-share application:
  Compute the profit ratio in the chip-distribution structure:
  - Profit ratio > 90% and shrinking volume -> winners are reluctant to sell -> may continue rising
  - Profit ratio > 90% and expanding volume -> winners are exiting -> topping signal
  - Profit ratio < 10% and shrinking volume -> low willingness to cut losses -> bottom stabilization
  - Profit ratio < 10% and expanding volume -> panic selling -> short-term oversold

Quant implementation:
  capital_gain_overhang = (current_price - avg_cost) / avg_cost
  where avg_cost is approximated by 60-day VWAP
  CGO > 0.2 -> strong unrealized gains, watch for disposition-effect selling pressure
  CGO < -0.3 -> deeply trapped holders, selling pressure may actually ease
```

### 2. Composite Sentiment Indicator

```python
# Multi-dimensional sentiment score (0-100, 50 = neutral)
sentiment_components = {
    'turnover_ratio': normalize(all_a_turnover, historical_percentile),      # weight 25%
    'margin_growth': normalize(monthly_margin_growth, historical_percentile), # weight 25%
    'new_high_ratio': normalize(new_high_ratio, historical_percentile),       # weight 20%
    'limit_up_count': normalize(limit_up_count, historical_percentile),       # weight 15%
    'fund_discount': normalize(closed_end_fund_discount, historical_percentile), # weight 15% (inverse)
}

sentiment_score = weighted_sum(components)
# > 80: extreme greed -> cut exposure below 60%
# 60-80: optimistic -> maintain normal exposure
# 40-60: neutral -> keep exposure unchanged
# 20-40: pessimistic -> add gradually
# < 20: extreme fear -> increase exposure above 80%
```

### 3. Behavioral Optimization of Momentum Strategies

Traditional momentum (sorting by past 12-month returns) is unstable in China A-shares. A behavioral-finance perspective suggests the following optimizations:

```
Optimization 1: Separate sentiment momentum from fundamental momentum
  Sentiment momentum = part of recent price rise with no fundamental support -> short-term reversal
  Fundamental momentum = price rise consistent with earnings revisions -> can persist
  Trade: buy stocks with "strong fundamental momentum + weak sentiment momentum"

Optimization 2: Attention-weighted momentum
  High-attention retail names reverse faster
  Indicator: if abnormal turnover > 3x average, cut momentum holding period by 50%
  Example: if a normal momentum basket holds for 60 days, high-attention names hold only 30 days

Optimization 3: Combine cross-sectional momentum and time-series momentum
  Cross-sectional: relative strength (top 20% in return ranking)
  Time-series: absolute trend (price > MA60)
  Both satisfied -> strong signal; only one satisfied -> half position
```

### 4. Contrarian Trading Signals

```
Extreme-fear buy conditions (at least 3 items):
  □ Shanghai Composite RSI(5) < 15
  □ All-A daily turnover < 0.5%
  □ Weekly margin-financing decline > 5%
  □ Limit-up count < 10 and limit-down count > 50
  □ Closed-end fund discount > 15%

Extreme-greed sell conditions (at least 3 items):
  □ Shanghai Composite RSI(5) > 90
  □ All-A daily turnover > 3%
  □ Weekly margin-financing growth > 10%
  □ Limit-up count > 150
  □ Weekly increase in new account openings > 100%
```

## Output Format

Behavioral-finance analysis report:
```
=== Market Sentiment Diagnosis ===
Date: 2026-03-28
Sentiment score: 72/100 (optimistic bias)
Current phase: transition from optimism to excitement

=== Behavioral-Bias Signals ===
Overreaction detection: 127 stocks rose > 15% in the past 5 days -> 65% probability of short-term reversal
Disposition effect: winner-clearing ratio is low (35%) -> overhead selling pressure remains
Herding effect: sector correlation 0.85 -> severe follow-the-leader behavior, divergence likely soon

=== Strategy Recommendations ===
Momentum strategy: shorten holding period from 60 days to 30 days (market attention is elevated)
Contrarian signal: not triggered (sentiment is not yet extreme)
Position suggestion: maintain 70% exposure, and prioritize names with "strong fundamental momentum + weak sentiment momentum"

=== Debiasing Checklist ===
□ Are you overconfident because of recent profits? -> check position concentration
□ Are you anchored to your entry price? -> re-evaluate using current PE/PB
□ Are you ignoring bearish information? -> force yourself to read bearish research reports
```

## Notes

1. **High retail participation in China A-shares**: behavioral-bias signals are more pronounced than in US equities, but sector rotation is also faster, so momentum windows should be shorter
2. **Lag in sentiment indicators**: margin-financing balance is released T+1, and new account openings are weekly, so they are not suitable for intraday trading
3. **Structural changes**: after 2019, foreign capital and quant participation rose, so the effectiveness of traditional behavioral-finance signals may have weakened
4. **Behavioral factors correlate with traditional factors**: disposition-effect factors correlate about 0.3-0.5 with momentum, so control collinearity
5. **Overfitting risk**: behavioral stories are easy to explain after the fact, so out-of-sample validation is mandatory
6. **Extreme sentiment is rare**: extreme fear / greed appears only 2-3 times per year, so strategy capacity is limited

## Dependencies

```bash
pip install pandas numpy scipy
```
