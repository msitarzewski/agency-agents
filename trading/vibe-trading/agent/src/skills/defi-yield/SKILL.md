---
name: defi-yield
description: DeFi yield analysis and optimization — lending rates, LP yields, staking returns, yield farming strategies, risk-adjusted yield comparison, and protocol-level sustainability assessment.
category: crypto
---
# DeFi Yield Analysis & Optimization

## Overview

Analyze and compare yields across DeFi protocols — lending, liquidity provision, staking, and yield farming — to identify the best risk-adjusted opportunities and assess sustainability. DeFi yields are a real-time proxy for crypto market leverage demand, capital allocation, and protocol health.

## Core Concepts

### 1. DeFi Yield Sources

| Yield Source | Mechanism | Typical APY Range | Risk Level |
|-------------|-----------|-------------------|------------|
| Lending (supply) | Earn interest from borrowers | 1-15% (stablecoins 3-8%) | Low-medium |
| Borrowing cost | Interest paid by borrowers | 3-20% | N/A (cost side) |
| LP fees (AMM) | Trading fee share from DEX | 5-50% (varies by pair) | Medium-high |
| Staking | Validator/delegation rewards | 3-15% | Low-medium |
| Liquidity mining | Protocol token incentives | 10-500% (unsustainable) | High |
| Restaking | Re-hypothecated staking yield | 5-20% (ETH + AVS rewards) | Medium-high |
| Points farming | Off-chain points → future airdrop | Unknown (speculative) | Very high |

### 2. Lending Rate Analysis

**Lending rates as market signal:**

```python
# High borrow rates = high leverage demand = bullish sentiment
# Low borrow rates = low leverage demand = bearish / waiting

def lending_rate_signal(borrow_rate_stable, borrow_rate_eth):
    """Analyze DeFi lending rates for market sentiment."""
    if borrow_rate_stable > 15:
        stable_signal = "extreme_demand"    # Leveraged long via stablecoin borrowing
    elif borrow_rate_stable > 8:
        stable_signal = "elevated_demand"
    elif borrow_rate_stable > 3:
        stable_signal = "normal"
    else:
        stable_signal = "low_demand"        # Bear market, no one borrowing

    if borrow_rate_eth > 10:
        eth_signal = "extreme_demand"       # Shorting or leveraged strategies
    elif borrow_rate_eth > 5:
        eth_signal = "elevated"
    else:
        eth_signal = "low_demand"

    return stable_signal, eth_signal
```

**Key lending protocols:**

| Protocol | Chain | Specialization | TVL Range |
|----------|-------|---------------|-----------|
| Aave V3 | Multi-chain | Blue-chip lending, institutional grade | $10-20B |
| Compound V3 | Ethereum, Base | Conservative, USDC-focused | $3-5B |
| MakerDAO/Sky | Ethereum | CDP-based DAI/USDS minting | $8-15B |
| Morpho | Ethereum | Rate optimization, P2P matching | $3-8B |
| Spark | Ethereum | MakerDAO lending arm | $2-5B |
| Kamino | Solana | Concentrated LP + lending | $1-3B |

### 3. LP Yield Analysis

**Impermanent Loss (IL) — the core risk of LP positions:**

```python
def impermanent_loss(price_ratio_change):
    """
    Calculate impermanent loss for a 50/50 AMM pool.
    price_ratio_change: new_price / old_price of the volatile asset.
    """
    r = price_ratio_change
    il = 2 * (r ** 0.5) / (1 + r) - 1
    return il * 100  # Return as percentage

# Examples:
# Price +25% → IL = -0.6%
# Price +50% → IL = -2.0%
# Price +100% (2x) → IL = -5.7%
# Price +200% (3x) → IL = -13.4%
# Price -50% → IL = -5.7%
# Price -75% → IL = -20.0%
```

**LP yield = fee income + token incentives - impermanent loss**

```python
def net_lp_yield(fee_apy, incentive_apy, estimated_il_annualized):
    """Calculate risk-adjusted LP yield."""
    gross_yield = fee_apy + incentive_apy
    net_yield = gross_yield - abs(estimated_il_annualized)
    return net_yield

# Example: ETH/USDC pool
# Fee APY: 15%, Incentive APY: 20%, Estimated IL: 8%
# Net yield: 15% + 20% - 8% = 27%
```

**LP pool evaluation criteria:**

| Metric | Good | Mediocre | Avoid |
|--------|------|----------|-------|
| Fee APY / TVL | > 10% | 5-10% | < 5% |
| IL risk (based on pair volatility) | < 5% annualized | 5-15% | > 15% |
| TVL stability (30d change) | Growing or stable | Declining < 10% | Declining > 30% |
| Volume/TVL ratio | > 0.5x daily | 0.1-0.5x | < 0.1x |
| Incentive dependency | < 30% of yield | 30-70% | > 70% (unsustainable) |

### 4. Staking Yield Analysis

**ETH staking ecosystem:**

| Method | APY | Risk | Liquidity |
|--------|-----|------|-----------|
| Solo validator | ~3.5% | Slashing, downtime | Locked (exit queue) |
| Lido (stETH) | ~3.3% | Smart contract, governance | Liquid (stETH tradeable) |
| Rocket Pool (rETH) | ~3.2% | Smart contract, more decentralized | Liquid |
| Coinbase (cbETH) | ~3.0% | Custodial, regulatory | Liquid |
| EigenLayer restaking | ~3.5% + AVS rewards | Smart contract, slashing risk | Semi-liquid |

**Staking yield signal:**
```python
# ETH staking yield trends
# Rising yield = more transactions / MEV = network activity increasing (bullish)
# Falling yield = less activity = network cooling down

# Restaking yield premium
restaking_premium = eigenlayer_yield - native_staking_yield
if restaking_premium > 3:
    signal = "high_restaking_demand"     # AVS demand strong
elif restaking_premium > 1:
    signal = "moderate_premium"
else:
    signal = "low_premium"               # Restaking risk not compensated
```

### 5. Yield Sustainability Assessment

**The "real yield" test:**

```python
def yield_sustainability(protocol):
    """
    Real yield = yield funded by actual economic activity (fees, revenue)
    Token yield = yield funded by token emissions (inflationary, unsustainable)
    """
    total_yield_usd = protocol.total_yield_distributed_per_year
    fee_revenue_usd = protocol.annual_fee_revenue
    token_emission_usd = protocol.annual_token_emissions_at_market_price

    real_yield_pct = fee_revenue_usd / total_yield_usd * 100
    token_yield_pct = token_emission_usd / total_yield_usd * 100

    if real_yield_pct > 80:
        sustainability = "highly_sustainable"   # Revenue-funded
    elif real_yield_pct > 50:
        sustainability = "partially_sustainable"
    elif real_yield_pct > 20:
        sustainability = "emission_dependent"    # Mostly token incentives
    else:
        sustainability = "ponzi_risk"            # Almost entirely token-funded

    return sustainability, real_yield_pct
```

**Warning signs of unsustainable yield:**
1. APY > 100% with no clear revenue source → token emissions will dilute to zero
2. Protocol TVL growing but token price declining → mercenary capital chasing yield
3. Yield declining month-over-month while TVL is stable → emissions being cut
4. Protocol governance voting to increase emissions → short-term pump, long-term dilution
5. Multiple yield sources stacking (lending + LP + staking + points) → complexity hides risk

### 6. Risk-Adjusted Yield Comparison Framework

```python
def risk_adjusted_yield(opportunities):
    """Compare DeFi opportunities on risk-adjusted basis."""
    scored = []
    for opp in opportunities:
        # Base yield
        base = opp.apy

        # Risk deductions
        smart_contract_risk = -2 if opp.audit_status == "unaudited" else -0.5
        il_risk = -opp.estimated_il if opp.type == "LP" else 0
        protocol_risk = -1 if opp.tvl < 50_000_000 else 0  # Small protocol risk
        chain_risk = -0.5 if opp.chain != "ethereum" else 0  # Non-ETH chain risk
        sustainability_risk = -(base * 0.3) if opp.real_yield_pct < 30 else 0

        # Adjusted yield
        adjusted = base + smart_contract_risk + il_risk + protocol_risk + chain_risk + sustainability_risk

        scored.append({
            "protocol": opp.name,
            "base_apy": base,
            "adjusted_apy": adjusted,
            "risk_level": opp.risk_level,
        })

    return sorted(scored, key=lambda x: x["adjusted_apy"], reverse=True)
```

## Data Sources

| Source | Access | Data Available |
|--------|--------|---------------|
| DeFi Llama Yields | Free | APY across 1000+ pools/protocols |
| Aave/Compound dashboards | Free | Real-time lending rates |
| Dune Analytics | Free | Custom yield queries |
| DeBank | Free | Portfolio yield tracking |
| TokenTerminal | Free/Paid | Protocol revenue and earnings |
| EigenLayer dashboard | Free | Restaking rates and AVS yields |

## Output Format

```
## DeFi Yield Analysis — [Date]

### Market Yield Overview
- **Stablecoin lending (Aave USDC)**: X.X% supply APY
- **ETH staking**: X.X% base + X.X% restaking premium
- **Top LP yields**: [pool1 X%, pool2 X%]
- **Yield trend**: [rising / stable / compressing]

### Top Opportunities (Risk-Adjusted)
| Rank | Protocol | Pool/Strategy | Base APY | Adjusted APY | Risk |
|------|----------|--------------|----------|-------------|------|
| 1 | [protocol] | [pool] | X.X% | X.X% | Low |
| 2 | [protocol] | [pool] | X.X% | X.X% | Medium |
| 3 | [protocol] | [pool] | X.X% | X.X% | Medium |

### Lending Market Signal
- **Stablecoin borrow rates**: X.X% → [high leverage demand / normal / low]
- **ETH borrow rates**: X.X% → [shorting demand / normal]
- **Utilization rates**: [high / normal / low]

### Sustainability Assessment
| Protocol | Real Yield % | Token Yield % | Verdict |
|----------|-------------|---------------|---------|
| [protocol] | XX% | XX% | Sustainable |
| [protocol] | XX% | XX% | Emission-dependent |

### Yield Strategy Recommendation
- **Conservative**: [stablecoin lending on Aave/Compound, X-X% APY]
- **Balanced**: [ETH staking + restaking, X-X% APY]
- **Aggressive**: [LP on DEX with hedged IL, X-X% net APY]

### Risk Warnings
1. [Smart contract risk: protocol X is unaudited]
2. [IL risk: volatile pair X/Y estimated IL X%]
3. [Sustainability risk: protocol Y >80% token-funded]
```

## Notes

- DeFi yields are highly variable and can change within hours; quoted APYs are point-in-time snapshots
- "APY" in DeFi often assumes compounding that requires manual action (claiming + restaking); true returns may be lower
- Smart contract risk is the dominant risk in DeFi; even audited protocols have been exploited (multi-sig, oracle manipulation)
- Tax implications of DeFi yield vary by jurisdiction; yield farming income is taxable in most countries
- This framework is for research purposes only and does not constitute investment advice
