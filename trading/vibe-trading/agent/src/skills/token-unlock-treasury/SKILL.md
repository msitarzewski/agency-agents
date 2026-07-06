---
name: token-unlock-treasury
description: Token unlock schedule analysis and project treasury tracking — vesting cliffs, linear unlocks, team/investor/ecosystem token releases, treasury diversification, and sell pressure forecasting.
category: crypto
---
# Token Unlock & Treasury Analysis

## Overview

Track token vesting schedules, upcoming unlock events, and project treasury holdings to forecast sell pressure and assess project sustainability. Token unlocks are one of the most predictable and high-impact supply-side events in crypto — large unlocks consistently create short-term selling pressure.

## Core Concepts

### 1. Token Distribution Taxonomy

**Standard allocation categories:**

| Category | Typical % | Lock Period | Vesting | Sell Pressure Risk |
|----------|-----------|------------|---------|-------------------|
| Team / Founders | 15-25% | 12-24 months cliff | 2-4 year linear | High (sell to fund lifestyle / diversify) |
| Investors (Seed) | 5-15% | 6-12 months cliff | 1-2 year linear | Very high (VC fund lifecycle: must return capital) |
| Investors (Series A+) | 10-20% | 6-12 months cliff | 1-2 year linear | Very high |
| Ecosystem / Community | 20-40% | Variable | Ongoing emissions | Medium (depends on incentive design) |
| Treasury / Foundation | 10-20% | None (discretionary) | DAO-governed | Low-medium (depends on governance) |
| Public Sale / Airdrop | 5-15% | None | Immediately liquid | Initial dump, then stabilizes |
| Advisors | 2-5% | 6-12 months cliff | 1-2 year linear | Medium |

### 2. Unlock Event Types

**Cliff unlock:**
- Large one-time release after lock period expires
- Most impactful: 5-30% of supply unlocking in a single event
- Typical impact: -5% to -20% price decline in the 7 days around a cliff unlock

**Linear / continuous unlock:**
- Steady stream of tokens released over time (daily/weekly/monthly)
- Creates persistent but predictable sell pressure
- Impact depends on rate relative to trading volume

**Milestone-based unlock:**
- Triggered by protocol metrics (TVL target, user count, etc.)
- Less predictable but usually positive signal (means protocol is growing)

### 3. Unlock Impact Assessment

```python
def assess_unlock_impact(unlock_amount, circulating_supply, daily_volume, recipient_type):
    """
    Assess the market impact of an upcoming token unlock.
    """
    # Unlock as % of circulating supply
    supply_pct = unlock_amount / circulating_supply * 100

    # Unlock as multiple of daily volume
    volume_multiple = unlock_amount / daily_volume

    # Base impact score
    if supply_pct > 10:
        base_impact = "critical"      # >10% of supply = very high impact
    elif supply_pct > 5:
        base_impact = "high"
    elif supply_pct > 2:
        base_impact = "medium"
    elif supply_pct > 0.5:
        base_impact = "low"
    else:
        base_impact = "negligible"

    # Adjust for recipient type (who receives the tokens)
    recipient_multiplier = {
        "team": 0.7,         # Team sells ~70% within 6 months historically
        "investor_seed": 0.8, # VCs must return capital, sell aggressively
        "investor_later": 0.6,
        "ecosystem": 0.3,    # Ecosystem tokens often re-staked or used
        "treasury": 0.2,     # Treasury rarely dumps (governance constraints)
        "community": 0.5,    # Mixed behavior
    }

    effective_sell_pressure = supply_pct * recipient_multiplier.get(recipient_type, 0.5)

    # Volume absorption capacity
    if volume_multiple > 5:
        absorption = "illiquid"       # Market cannot absorb easily
    elif volume_multiple > 2:
        absorption = "difficult"
    elif volume_multiple > 0.5:
        absorption = "manageable"
    else:
        absorption = "easily_absorbed"

    return {
        "supply_impact_pct": supply_pct,
        "base_impact": base_impact,
        "effective_sell_pct": effective_sell_pressure,
        "volume_absorption": absorption,
    }
```

### 4. Historical Unlock Price Patterns

**Empirical observations (2021-2025 data):**

| Unlock Size (% of circ.) | Pre-unlock (7d) | Post-unlock (7d) | Post-unlock (30d) |
|--------------------------|-----------------|------------------|-------------------|
| >10% | -8 to -15% | -5 to -20% | -10 to -30% (often no recovery) |
| 5-10% | -3 to -8% | -3 to -10% | Mixed (depends on market regime) |
| 2-5% | -1 to -5% | -2 to -5% | Usually recovers within 30d |
| <2% | Minimal | -1 to -3% | Negligible long-term impact |

**Key patterns:**
1. **Pre-unlock front-running**: market starts selling 3-7 days before known unlock dates
2. **Post-unlock recovery**: if broader market is bullish, 2-5% unlocks often fully recover within 2-4 weeks
3. **Continuous unlock drag**: tokens with >5% monthly emission rate tend to underperform BTC by 10-20% annualized
4. **Cliff + bear market = disaster**: large cliff unlocks during bear markets create cascading selling

### 5. Treasury Health Analysis

**Treasury assessment framework:**

```python
treasury_health = {
    "total_value_usd": 500_000_000,       # Total treasury value
    "runway_months": 36,                   # Treasury / monthly burn
    "diversification": {
        "native_token_pct": 60,            # % held in own token (risky)
        "stablecoins_pct": 25,             # USDC/USDT/DAI (safe)
        "eth_btc_pct": 10,                 # Blue-chip crypto
        "other_pct": 5,                    # Other assets
    },
    "monthly_burn_usd": 5_000_000,         # Operating expenses per month
    "revenue_coverage": 0.6,               # Revenue / burn ratio
}

def treasury_signal(health):
    # Runway assessment
    if health["runway_months"] < 12:
        runway_signal = "critical"         # Less than 1 year of funding
    elif health["runway_months"] < 24:
        runway_signal = "concerning"
    else:
        runway_signal = "healthy"

    # Diversification assessment
    native_pct = health["diversification"]["native_token_pct"]
    if native_pct > 80:
        diversity_signal = "concentrated_risk"  # Treasury value crashes with token price
    elif native_pct > 50:
        diversity_signal = "moderate_risk"
    else:
        diversity_signal = "diversified"        # Healthy treasury management

    # Revenue sustainability
    if health["revenue_coverage"] > 1.0:
        revenue_signal = "self_sustaining"      # Revenue covers all expenses
    elif health["revenue_coverage"] > 0.5:
        revenue_signal = "partially_funded"
    else:
        revenue_signal = "treasury_dependent"   # Fully reliant on treasury

    return runway_signal, diversity_signal, revenue_signal
```

**Red flags in treasury management:**
1. Treasury >80% in native token → death spiral risk (token drops → treasury drops → must sell more)
2. Runway < 12 months → protocol may cut development or do emergency token sale
3. Large OTC sales by treasury → dilution signal (often sold at 20-30% discount)
4. Treasury spending on non-core activities (acquisitions, marketing burns) → poor capital allocation
5. No revenue or declining revenue → unsustainable token emissions subsidizing usage

### 6. Emission Rate Analysis

```python
def emission_analysis(token):
    """Analyze ongoing token emission sustainability."""
    # Monthly emission rate
    monthly_new_tokens = token.monthly_unlock + token.staking_rewards + token.mining_rewards
    monthly_emission_pct = monthly_new_tokens / token.circulating_supply * 100

    # Inflation-adjusted real yield
    staking_yield_nominal = token.staking_apy
    inflation_rate = monthly_emission_pct * 12  # Annualized
    real_yield = staking_yield_nominal - inflation_rate

    # Assessment
    if monthly_emission_pct > 5:
        emission_verdict = "hyperinflation"    # Unsustainable
    elif monthly_emission_pct > 2:
        emission_verdict = "high_inflation"    # Significant dilution
    elif monthly_emission_pct > 0.5:
        emission_verdict = "moderate"          # Manageable
    else:
        emission_verdict = "low_emission"      # Minimal dilution

    if real_yield < 0:
        yield_verdict = "negative_real_yield"  # Staking rewards < inflation = value destruction
    else:
        yield_verdict = "positive_real_yield"

    return emission_verdict, yield_verdict, real_yield
```

### 7. Major Protocol Unlock Calendars

**Tier 1 protocols to track:**

| Protocol | Token | Key Unlock Events | Data Source |
|----------|-------|-------------------|-------------|
| Solana | SOL | Foundation + early investor unlocks | Token Unlocks |
| Aptos | APT | Monthly investor/team unlocks | Token Unlocks |
| Arbitrum | ARB | Massive team + investor cliff (Mar 2025) | Token Unlocks |
| Sui | SUI | Investor and contributor unlocks | Token Unlocks |
| Celestia | TIA | Investor cliff unlock | Token Unlocks |
| Starknet | STRK | Large early investor vesting | Token Unlocks |
| Optimism | OP | Ongoing core contributor vesting | Token Unlocks |
| dYdX | DYDX | Trading rewards + team vesting | Token Unlocks |

**Data sources:**
- tokenunlocks.app — most comprehensive unlock calendar
- messari.io/asset/{token}/profile — tokenomics breakdown
- Protocol governance forums — treasury proposals and spending

## Output Format

```
## Token Unlock & Treasury Analysis — [Protocol/Token]

### Tokenomics Overview
- **Total supply**: X,XXX,XXX,XXX
- **Circulating supply**: X,XXX,XXX,XXX (X% of total)
- **Fully diluted valuation (FDV)**: $X.XB
- **Market cap / FDV ratio**: X.X% (lower = more future dilution)

### Upcoming Unlocks (next 90 days)
| Date | Amount | % of Circ. | Recipient | Impact |
|------|--------|-----------|-----------|--------|
| YYYY-MM-DD | X,XXX,XXX | X.X% | Team | High |
| YYYY-MM-DD | X,XXX,XXX | X.X% | Investor | Medium |

### Emission Rate
- **Monthly new supply**: X.X% of circulating
- **Annualized inflation**: X.X%
- **Staking nominal yield**: X.X%
- **Real yield (yield - inflation)**: X.X%
- **Verdict**: [hyperinflation / high / moderate / low]

### Treasury Health
- **Total value**: $XXX M
- **Composition**: X% native token, X% stablecoins, X% ETH/BTC
- **Monthly burn**: $X.X M
- **Runway**: XX months
- **Revenue coverage**: X.X%
- **Diversification risk**: [concentrated / moderate / diversified]

### Sell Pressure Forecast
- **Next 30 days**: [X tokens unlocking → $X.XM at current price → X days of volume]
- **Next 90 days**: [summary]
- **Absorption capacity**: [easily / manageable / difficult / illiquid]

### Signal
- **Short-term (pre-unlock)**: [avoid / reduce / hold / accumulate]
- **Medium-term (post-unlock)**: [recovery expected / persistent pressure / unclear]
- **Long-term (tokenomics health)**: [sustainable / concerning / unsustainable]
```

## Notes

- Token unlock data requires external sources (tokenunlocks.app, protocol docs); not available via OKX API
- Unlock dates can change if governance votes to modify vesting schedules
- Market cap / FDV ratio < 30% means >70% of tokens are still locked — significant future dilution risk
- Always compare unlock impact relative to daily trading volume, not just supply percentage
- Some protocols have buyback / burn mechanisms that offset emissions — check net inflation, not gross
- This framework is for research purposes only and does not constitute investment advice
