---
name: liquidation-heatmap
description: Liquidation level analysis and heatmap interpretation — identify leveraged position concentration, liquidation cascades, stop-hunt zones, and use liquidation data as support/resistance signals.
category: crypto
---
# Liquidation Heatmap & Level Analysis

## Overview

Analyze the distribution of leveraged positions and their liquidation price levels to identify zones where forced selling/buying will accelerate price moves. Liquidation clusters act as "magnets" — price tends to be attracted toward large liquidation concentrations because market makers and whales profit from triggering cascading liquidations.

## Core Concepts

### 1. Liquidation Mechanics

**How liquidation works:**

```python
# Long position liquidation
long_liquidation_price = entry_price * (1 - 1/leverage + maintenance_margin)

# Short position liquidation
short_liquidation_price = entry_price * (1 + 1/leverage - maintenance_margin)

# Example: BTC long at $65,000, 10x leverage, 0.5% maintenance margin
# Liquidation: $65,000 * (1 - 1/10 + 0.005) = $58,825
# A 9.5% move against the position triggers liquidation
```

**Leverage and liquidation distance:**

| Leverage | Liquidation Distance (Long) | Liquidation Distance (Short) |
|----------|----------------------------|------------------------------|
| 2x | ~50% drop | ~50% rise |
| 5x | ~20% drop | ~20% rise |
| 10x | ~10% drop | ~10% rise |
| 20x | ~5% drop | ~5% rise |
| 50x | ~2% drop | ~2% rise |
| 100x | ~1% drop | ~1% rise |

### 2. Liquidation Heatmap Interpretation

A liquidation heatmap shows where liquidation orders are concentrated across different price levels, typically color-coded by density.

**Reading the heatmap:**

```
Price Level    Long Liquidations    Short Liquidations    Interpretation
$70,000        ░░░░░░░░░░          ████████████████      Heavy short liquidation zone
$68,000        ░░░░                ██████████            Moderate short liquidation
$66,000        ███████             ███████               Balanced (current price area)
$64,000        ██████████          ░░░░                  Moderate long liquidation
$62,000        ████████████████    ░░░░░░░░░░            Heavy long liquidation zone
```

**Key principles:**
1. **Liquidation clusters are magnets**: price tends to gravitate toward large liquidation pools because the forced orders provide liquidity for whales to fill their positions
2. **Liquidation cascades**: when a cluster gets hit, the forced selling/buying pushes price further, potentially triggering the next cluster → cascade effect
3. **After liquidation wipe**: once a large cluster is liquidated, that price level often becomes support/resistance (overleveraged positions are gone)

### 3. Liquidation Level Identification

```python
def identify_liquidation_clusters(open_interest_by_price, leverage_distribution):
    """
    Estimate where liquidation clusters exist based on
    open interest and leverage distribution.
    """
    clusters = []

    for price_level in price_range:
        # Long liquidations: positions opened above this level with high leverage
        long_liq_volume = estimate_long_liq_at_price(
            open_interest_by_price, leverage_distribution, price_level
        )

        # Short liquidations: positions opened below this level with high leverage
        short_liq_volume = estimate_short_liq_at_price(
            open_interest_by_price, leverage_distribution, price_level
        )

        total = long_liq_volume + short_liq_volume

        if total > significance_threshold:
            clusters.append({
                "price": price_level,
                "long_liq": long_liq_volume,
                "short_liq": short_liq_volume,
                "type": "long" if long_liq_volume > short_liq_volume else "short",
                "magnitude": total,
            })

    return sorted(clusters, key=lambda x: x["magnitude"], reverse=True)
```

### 4. Liquidation-Based Trading Signals

**Signal 1: Liquidation Magnet**
```python
def liquidation_magnet_signal(current_price, clusters):
    """
    Price is likely to move toward the nearest large liquidation cluster.
    """
    # Find nearest cluster above and below
    above = [c for c in clusters if c["price"] > current_price]
    below = [c for c in clusters if c["price"] < current_price]

    nearest_above = min(above, key=lambda c: c["price"] - current_price) if above else None
    nearest_below = min(below, key=lambda c: current_price - c["price"]) if below else None

    if nearest_above and nearest_below:
        above_magnitude = nearest_above["magnitude"]
        below_magnitude = nearest_below["magnitude"]

        if above_magnitude > below_magnitude * 2:
            return "upward_magnet"      # Larger cluster above → price likely moves up
        elif below_magnitude > above_magnitude * 2:
            return "downward_magnet"    # Larger cluster below → price likely moves down
        else:
            return "balanced"           # Both sides have similar clusters
```

**Signal 2: Cascade Risk**
```python
def cascade_risk(current_price, clusters, direction="down"):
    """
    Assess risk of liquidation cascade — multiple clusters stacked close together.
    """
    if direction == "down":
        relevant = sorted([c for c in clusters if c["price"] < current_price and c["type"] == "long"],
                         key=lambda c: c["price"], reverse=True)
    else:
        relevant = sorted([c for c in clusters if c["price"] > current_price and c["type"] == "short"],
                         key=lambda c: c["price"])

    if len(relevant) < 2:
        return "low_cascade_risk"

    # Check if clusters are stacked within 5% of each other
    gaps = []
    for i in range(len(relevant) - 1):
        gap = abs(relevant[i]["price"] - relevant[i+1]["price"]) / current_price * 100
        gaps.append(gap)

    if min(gaps) < 2:
        return "high_cascade_risk"      # Clusters stacked tightly → cascade likely
    elif min(gaps) < 5:
        return "moderate_cascade_risk"
    else:
        return "low_cascade_risk"
```

**Signal 3: Post-Liquidation Support/Resistance**
```python
def post_liquidation_sr(price_history, liquidation_events):
    """
    After a large liquidation event, that price level often becomes S/R.
    """
    sr_levels = []
    for event in liquidation_events:
        if event.total_liquidated > 100_000_000:  # >$100M liquidated
            sr_levels.append({
                "price": event.price_level,
                "type": "support" if event.liquidation_type == "long" else "resistance",
                "strength": event.total_liquidated,
                "date": event.date,
            })
    return sr_levels
```

### 5. Liquidation Data Metrics

**Key metrics to track:**

| Metric | Description | Signal |
|--------|-------------|--------|
| 24h total liquidations | Total USD liquidated across all exchanges | > $500M = extreme, volatility spike |
| Long/Short liquidation ratio | Longs liquidated / Shorts liquidated | > 2 = longs squeezed, < 0.5 = shorts squeezed |
| Largest single liquidation | Biggest individual position liquidated | > $10M = whale liquidation |
| OI change post-liquidation | Open interest change after event | Large OI drop = leverage washed out (healthy) |
| Exchange-specific liquidation | Which exchange had most liquidations | Indicates where leverage is concentrated |

**Liquidation volume interpretation:**

| 24h Liquidations | Market State | Implication |
|-----------------|-------------|-------------|
| > $1B | Extreme event | Major leverage wipeout, potential V-reversal |
| $500M - $1B | High volatility | Significant positioning reset |
| $200M - $500M | Elevated | Moderate leverage reduction |
| $50M - $200M | Normal | Background noise |
| < $50M | Calm | Low volatility, leverage building |

### 6. Liquidation Cascade Anatomy

**Typical cascade sequence:**

```
1. Initial trigger (macro event, whale selling, technical breakdown)
   ↓
2. Price hits first liquidation cluster ($65,000)
   → $200M in long liquidations forced to sell
   ↓
3. Forced selling pushes price to next cluster ($63,000)
   → $300M more in long liquidations
   ↓
4. Cascade accelerates → high-leverage positions ($62,000-$60,000)
   → $500M in rapid succession
   ↓
5. Eventually: open interest drops 20-30%, funding rate flips negative
   → Leverage is "washed out" → bottom forms
   ↓
6. Recovery begins (short-term) as no more forced sellers remain
```

**Trading around cascades:**
- **Before cascade**: reduce leverage, set wider stops, avoid high-leverage longs near heavy liquidation zones
- **During cascade**: do NOT try to catch the knife; wait for OI to stabilize
- **After cascade**: when funding rate flips deeply negative + OI has dropped 20%+, contrarian long entry with tight risk

### 7. Exchange-Level Liquidation Differences

| Exchange | Liquidation Engine | Key Feature |
|----------|-------------------|-------------|
| OKX | Tiered auto-deleveraging | Partial liquidation (reduce position size, not full close) |
| Binance | Insurance fund + ADL | Largest insurance fund (~$1B+) reduces cascade severity |
| Bybit | ADL (Auto-Deleveraging) | ADL triggers when insurance fund depleted |
| dYdX | On-chain liquidation | Transparent, anyone can liquidate (MEV opportunity) |

## Data Sources

| Source | Access | Data Available |
|--------|--------|---------------|
| CoinGlass | Free (limited) | Liquidation heatmap, 24h liquidations, OI |
| Laevitas | Free/Paid | Options + futures liquidation levels |
| Kingfisher (Coinalyze) | Paid | Real-time liquidation level estimates |
| Hyblock Capital | Paid | Professional liquidation heatmaps |
| OKX API | Free | Historical liquidation data |
| DeFi Llama | Free | DeFi protocol liquidation data |

## Output Format

```
## Liquidation Analysis — [Asset] — [Date]

### Liquidation Overview (24h)
- **Total liquidated**: $XXX M
- **Long liquidated**: $XXX M (XX%)
- **Short liquidated**: $XXX M (XX%)
- **Largest single**: $XX M [exchange]
- **Market state**: [extreme / elevated / normal / calm]

### Key Liquidation Levels
| Price Level | Type | Est. Volume | Distance from Current | Priority |
|------------|------|-------------|----------------------|----------|
| $XX,XXX | Short liq cluster | $XXX M | +X.X% | High |
| $XX,XXX | Long liq cluster | $XXX M | -X.X% | High |
| $XX,XXX | Long liq cluster | $XXX M | -X.X% | Medium |

### Heatmap Summary
- **Strongest upside magnet**: $XX,XXX (short liquidation cluster, $XXX M)
- **Strongest downside magnet**: $XX,XXX (long liquidation cluster, $XXX M)
- **Asymmetry**: [upside magnet stronger / downside stronger / balanced]

### Cascade Risk
- **Downside cascade risk**: [high / moderate / low]
  - [X clusters stacked within X% below current price]
- **Upside cascade risk**: [high / moderate / low]

### Post-Liquidation S/R Levels
- **Recent support formed**: $XX,XXX (long liquidation wipeout on DATE)
- **Recent resistance formed**: $XX,XXX (short liquidation wipeout on DATE)

### Trading Implications
- **Bias**: [upward magnet stronger → mild bullish / downward → bearish]
- **Risk**: [high leverage zone within X% → reduce position size]
- **Key level**: [$XX,XXX — if broken, cascade risk activates]
```

## Notes

- Liquidation data is estimated, not exact — exchanges do not publish real-time liquidation level details for all users
- Heatmap providers use statistical models based on OI and leverage distribution to estimate liquidation prices
- Liquidation levels shift constantly as traders open/close positions — treat as dynamic zones, not fixed prices
- "Stop hunts" (price briefly touching a liquidation cluster then reversing) are common — market makers deliberately trigger clusters
- DeFi liquidations are fully transparent (on-chain) but CEX liquidations are opaque
- This framework is for research purposes only and does not constitute investment advice
