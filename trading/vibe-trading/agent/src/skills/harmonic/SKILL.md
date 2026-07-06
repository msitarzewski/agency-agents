---
name: harmonic
description: Harmonic Patterns signal engine. Identifies XABCD five-point structures such as Gartley/Bat/Butterfly/Crab based on Fibonacci geometry, and generates trading signals in the PRZ (Potential Reversal Zone).
category: strategy
---
# Harmonic Patterns

## Purpose

The Fibonacci geometry school uses precise ratio relationships to identify price patterns:

| Pattern | B-Point Retracement | D-Point Retracement | Direction |
|------|---------|---------|------|
| Gartley | 0.618 XA | 0.786 XA | Reversal |
| Bat | 0.382-0.5 XA | 0.886 XA | Reversal |
| Butterfly | 0.786 XA | 1.27 XA | Reversal |
| Crab | 0.382-0.618 XA | 1.618 XA | Reversal |

## Core Concepts

- **XABCD five-point pattern**: a price structure defined by precise Fibonacci ratios
- **PRZ (Potential Reversal Zone)**: the convergence area around point D, where reversal probability is high
- Bullish pattern (point D at the bottom) → buy signal
- Bearish pattern (point D at the top) → sell signal

## Dependencies

```bash
pip install "vibe-trading-ai[harmonic]"
```

`pyharmonics` is optional. If the extra is not installed, the example signal
engine falls back to the bundled detector.

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| is_stock | False | Whether the instrument is a stock (affects analysis parameters) |

## Signal Convention

- `1` = long, `-1` = short, `0` = stand aside
