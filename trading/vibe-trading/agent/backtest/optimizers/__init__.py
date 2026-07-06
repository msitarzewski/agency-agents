"""Portfolio optimizer package.

Provides four weighting schemes:
- equal_volatility: inverse-volatility weights
- risk_parity: equal risk contribution (Spinu-style)
- mean_variance: max Sharpe via scipy
- max_diversification: maximize diversification ratio

Select via ``optimizer`` in ``config.json``; default is off (1/N).
Add a new optimizer by dropping a module here that exposes ``optimize()``.
"""
