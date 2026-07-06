---
name: onchain-analysis
description: On-chain data analysis — active addresses / whale tracking / TVL / DEX liquidity, interpretation and signal generation using on-chain valuation metrics such as MVRV / NVT / SOPR.
category: crypto
---

# On-Chain Data Analysis

## Overview

Use transparent public blockchain data for analysis, covering network activity, whale-behavior tracking, DeFi liquidity analysis, and on-chain valuation metrics. This provides crypto investing with data dimensions unavailable in traditional finance.

## Network Activity Metrics

### Core Activity Indicators

| Metric | Meaning | Bullish Signal | Bearish Signal |
|------|------|---------|---------|
| Active addresses | Unique addresses interacting with the network each day | Sustained increase (network adoption rising) | Sustained decline |
| New addresses | Addresses appearing for the first time each day | Accelerating growth (new users entering) | Shrinkage |
| Transaction count | Number of on-chain transactions per day | Steady growth | Sharp decline |
| Transfer value | Total value transferred on-chain per day | Large-value transfer activity | Inactive |
| Activity / price ratio | Growth in active addresses vs growth in price | Activity growth outpaces price growth | Price rises but activity does not |

### Activity Analysis Framework

```
Healthy bull market:
  Price↑ + active addresses↑ + new addresses↑ = driven by real demand

Bubble signal:
  Price↑ + active addresses↓ or flat = capital-driven, not user-driven

Bottoming signal:
  Price↓ + active addresses bottom out and stabilize = speculators exit, real users remain
```

### Historical Reference for BTC Active Addresses

| Phase | Active Addresses (daily avg) | BTC Price | Meaning |
|------|--------------|---------|------|
| 2020 bear-to-bull transition | 0.8-1.0 million | $10k-$20k | Bottom stabilization |
| 2021 bull market | 1.0-1.3 million | $30k-$69k | Healthy growth |
| 2022 bear market | 0.8-0.9 million | $16k-$30k | Pulled back but did not collapse |
| 2024 bull market | 0.9-1.2 million | $40k-$100k | Institution-driven |

## Whale Tracking

### Whale Definition

| Tier | BTC Holdings | ETH Holdings | Estimated Count |
|------|---------|---------|---------|
| Super whales | >10,000 BTC | >100,000 ETH | ~100 |
| Large whales | 1,000-10,000 BTC | 10,000-100,000 ETH | ~2,000 |
| Mid whales | 100-1,000 BTC | 1,000-10,000 ETH | ~15,000 |
| Small whales | 10-100 BTC | 100-1,000 ETH | ~150,000 |

### Whale Behavior Signals

```
Bullish signals:
1. Whales withdraw from exchanges -> intent to hold long term
2. Whale-wallet count rises -> institutions / large holders accumulating
3. Exchange BTC balance keeps falling -> lower available supply
4. Long-term holder (LTH) balances rise -> smart money buying

Bearish signals:
1. Large whale transfers into exchanges -> preparing to sell
2. Dormant addresses wake up and transfer -> early holders taking profits
3. Exchange balances surge -> sell pressure is about to be released
4. Miner balances fall and move to exchanges -> miner capitulation / profit taking
```

### Large Transfer Monitoring

```
Thresholds to watch:
- BTC: single transfer > 500 BTC (about $50M)
- ETH: single transfer > 10,000 ETH (about $30M)
- USDT: single transfer > $50M

Transfer-direction analysis:
- Wallet -> exchange: potential selling (bearish)
- Exchange -> wallet: withdrawal to hold (bullish)
- Exchange -> exchange: arbitrage transfer (neutral)
- Wallet -> wallet: OTC trade (watch follow-up behavior)
```

## DeFi Liquidity Analysis

### TVL (Total Value Locked)

```
TVL = total value of assets locked in DeFi protocols

TVL analysis dimensions:
1. Total TVL trend: rising = capital flowing into the DeFi ecosystem
2. Cross-chain TVL: market-share changes among ETH vs Solana vs Arbitrum
3. Protocol TVL ranking: leading protocols such as Aave / Lido / Maker
4. TVL / market cap ratio: similar to asset-utilization rate in traditional finance
```

### DEX Liquidity Metrics

| Metric | Meaning | Focus |
|------|------|--------|
| DEX volume | Daily decentralized-exchange volume | Trend in DEX / CEX ratio |
| Liquidity depth | Size of AMM liquidity pools | Bigger pools = lower slippage = better |
| LP yield | Annualized return for liquidity providers | Abnormally high = unsustainable |
| Impermanent loss | Opportunity cost for LPs | More severe when volatility is higher |

### Stablecoin Liquidity

```
Stablecoin inflows = "dry powder" for the crypto market

Metrics to watch:
1. Changes in total USDT / USDC supply
2. Stablecoin balances on exchanges
3. Stablecoin mint / burn activity (Tether / Circle)
4. Stablecoin market-cap share (lower = higher risk appetite)

Signals:
- Heavy stablecoin minting -> capital preparing to enter
- Exchange stablecoin balances up -> buying power is accumulating
- Stablecoin share rising quickly -> risk-off market (capital rotating from coins into stablecoins)
```

## On-Chain Valuation Metrics

### MVRV (Market Value to Realized Value)

```
MVRV = market cap / realized cap

Realized cap = Σ(each UTXO × price at last movement)
             = sum of all holders' cost basis

| MVRV | Meaning | Historical Signal |
|------|------|---------|
| > 3.5 | Severely overvalued, large unrealized profits across holders | Historical top zone |
| 2.0-3.5 | Richly valued, most holders in profit | Mid-to-late bull market |
| 1.0-2.0 | Reasonable range | Normal market or early bull market |
| < 1.0 | Undervalued, most holders underwater | Bear-market bottom zone |

Signal logic: MVRV > 3.5 -> most holders have large unrealized gains -> strong incentive to sell -> potential top
              MVRV < 1.0 -> most holders are losing money -> unwilling to sell -> potential bottom
```

### NVT (Network Value to Transactions)

```
NVT = market cap / daily on-chain transfer value

Similar to a PE ratio in traditional finance:
- High NVT: market cap is high relative to on-chain activity (overvalued or optimistic on future growth)
- Low NVT: market cap is low relative to on-chain activity (undervalued or value-like)

NVT Signal (improved):
NVT_Signal = market cap / MA(90, daily on-chain transfer value)
Use a 90-day moving average to smooth noise

| NVT Signal | Meaning |
|-----------|------|
| > 150 | Severely overvalued |
| 65-150 | Normal range |
| < 65 | Undervalued |
```

### SOPR (Spent Output Profit Ratio)

```
SOPR = realized value of spent outputs / creation value of spent outputs

Simply put: on average, are the coins sold today being sold at a profit or a loss?

| SOPR | Meaning | Signal |
|------|------|------|
| > 1.05 | Sellers are realizing 5%+ profit on average | Profit-taking pressure |
| 1.0-1.05 | Small-profit selling | Normal |
| = 1.0 | Break-even | Key support / resistance |
| < 1.0 | Selling at a loss | Panic selling (bottom signal) |

In bull markets: a pullback to SOPR = 1.0 is a buy opportunity (cost-basis support)
In bear markets: a rebound to SOPR = 1.0 is a sell opportunity (cost-basis resistance)
```

### Other On-Chain Valuation Metrics

| Metric | Formula | Purpose |
|------|------|------|
| Puell Multiple | Daily miner revenue / MA(365, daily miner revenue) | Miner-income cycle |
| Stock-to-Flow | stock / annual production | BTC scarcity model |
| Reserve Risk | HODL Bank / price | Holder confidence |
| Exchange balance | total BTC held on exchanges | Supply-side pressure |

## Analysis Framework

### Composite On-Chain Score

```
Score each indicator from 1 to 5 and combine with weights:

| Dimension | Weight | Indicators |
|------|------|------|
| Valuation | 30% | MVRV, NVT |
| Activity | 25% | active addresses, new addresses |
| Capital flow | 25% | exchange balances, stablecoins |
| Whale behavior | 20% | whale holdings, large transfers |

Total score > 4.0: strongly bullish
Total score 3.0-4.0: bullish bias
Total score 2.0-3.0: neutral
Total score < 2.0: bearish / leaning bearish
```

## Output Format

```markdown
## On-Chain Analysis Report: BTC

### On-Chain Snapshot
| Metric | Current Value | Historical Percentile | Signal |
|------|--------|---------|------|
| MVRV | 2.1 | 65% | Elevated but not at a top |
| NVT Signal | 85 | 50% | Fair |
| SOPR(7d avg) | 1.02 | 55% | Slight profit-taking state |
| Active addresses | 950k/day | 45% | Relatively low |
| Exchange balance | 2.30M BTC | 30% | Low level (bullish) |

### Whale Activity
- Last 7 days: net withdrawal of +15,000 BTC (bullish)
- Large transfers: 3 transfers >1000 BTC into cold wallets
- Miners: holdings stable, no major outflows observed

### Composite Score: 3.5/5 (bullish bias)

### Conclusion
On-chain data is broadly bullish. MVRV is not yet in an extreme zone, exchange balances are low,
and whales continue to accumulate. But active addresses remain soft, so monitor whether this is an
"institution-driven bull market without retail participation". Maintain long exposure, but keep
position sizing controlled and avoid leverage.
```

## Notes

1. **Data-source limitations**: on-chain data is most reliable for BTC and ETH; data quality for other chains is uneven
2. **Entity identification is difficult**: one entity can control multiple addresses, so whale analysis contains error
3. **UTXO vs account model**: BTC (UTXO) analysis methods cannot be directly applied to ETH (account model)
4. **Missing Layer-2 data**: many transactions occur on L2s (Arbitrum / Optimism), so L1 data is incomplete
5. **On-chain data lag**: block confirmation takes time, so this is not suitable for short-term trading decisions
6. **Data acquisition**: the built-in OKX data source provides candles / trade data, but on-chain data requires extra APIs (Glassnode / Nansen)
7. **Metric desensitization**: as market structure changes (ETFization / institutionalization), historical thresholds may need adjustment
