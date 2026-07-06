---
name: multi-factor
description: Multi-factor cross-sectional stock ranking. Combines factor standardization, equal-weight or IC-weighted scoring, and TopN portfolio construction. Suitable for multi-instrument portfolio strategies.
category: strategy
---
# Multi-Factor Cross-Sectional Stock Ranking

## Purpose

On the same time cross-section, compute multiple factor values for many stocks, standardize them, combine them into a composite score, and select the top-ranked stocks to build a portfolio.

## Signal Logic

1. **Factor calculation**: calculate N factors for each stock (such as momentum, value, and quality)
2. **Cross-sectional standardization**: standardize each factor on the cross-section with Z-score normalization (subtract mean, divide by standard deviation)
3. **Composite scoring**: sum the factors with equal weights (or custom weights) to obtain a composite score
4. **Rank and select**: go long the TopN names, with weight = 1/N for each

## Built-In Factors

| Factor Name | Calculation Method | Direction |
|--------|---------|------|
| momentum | Return over the past N days | Positive (higher is better) |
| reversal | Return over the past 5 days | Negative (lower is better) |
| volatility | Standard deviation of returns over the past N days | Negative (lower is better) |
| volume_ratio | Today's volume / N-day average volume | Positive |

If `extra_fields` are available (China A-shares), you can also add:
- `pe_factor`: 1/PE (the larger, the cheaper)
- `pb_factor`: 1/PB
- `roe_factor`: ROE (the larger, the better)

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| momentum_window | 20 | Momentum lookback window |
| vol_window | 20 | Volatility lookback window |
| top_n | 3 | Number of selected stocks |
| rebalance_freq | 20 | Rebalancing frequency (trading days) |

## Common Pitfalls

- Cross-sectional standardization requires at least 3 stocks, otherwise Z-scores are meaningless
- Keep the previous signal unchanged between rebalance dates (do not rerank every day)
- Factors have different directions: momentum is positively sorted, volatility is negatively sorted, so directions must be aligned before standardization
- Portfolio weights must be normalized: each TopN stock gets 1/N, all others get 0

## Dependencies

```bash
pip install pandas numpy
```

## Signal Convention

- `1/N` = selected into TopN (equal-weight long), `0` = not selected

## Zoo Signal Engine (new in 0.1.8)

When the user wants to compose 1-N alphas drawn from the Alpha Zoo (450+ pre-built factors) into a multi-factor strategy, use `ZooSignalEngine.from_zoo(...)` from `zoo_signal_engine.py` instead of the old per-symbol `example_signal_engine.py`. The new engine operates on wide-panel `dict[str, pd.DataFrame]` inputs (the same shape the registry's `Alpha.compute(panel)` contract uses), redistributes weights when any alpha fails or is skipped, and supports long-only (`top_n`), short-only (`bottom_n`), and long-short (`top_n` + `bottom_n`) signal modes. It also exposes a `generate(data_map)` adapter so it drops straight into the existing `run_backtest` pipelines.

```python
from src.factors.registry import Registry
from zoo_signal_engine import ZooSignalEngine

registry = Registry()
# Browse candidates with registry.list(theme="momentum") -- see the alpha-zoo skill.
alpha_ids = ["alpha101_001", "alpha101_012", "guotai_191_003"]
engine = ZooSignalEngine.from_zoo(alpha_ids, top_n=10, bottom_n=10, standardize=True)
# Feed into a panel-aware backtest, or via .generate(data_map) into the bundled engines.
signal_panel = engine.compute_signal(panel)  # DataFrame, same shape as panel["close"]
```

Cross-references:
- See the `alpha-zoo` skill for browsing the alpha catalogue, filtering by `theme`/`universe`, and inspecting `__alpha_meta__` records.
- `example_signal_engine.py` is kept for legacy per-symbol workflows that compute factors directly from raw OHLCV; **new code should prefer `zoo_signal_engine.py`** so it benefits from the 450+ zoo alphas, registry-level NaN/inf guardrails, and per-alpha skip isolation.

