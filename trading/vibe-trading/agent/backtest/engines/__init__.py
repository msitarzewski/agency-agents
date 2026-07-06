"""Backtest engines.

Wave 1 (v1):
  - BaseEngine: ABC for bar-by-bar execution with market rules
  - ChinaAEngine: A-share (T+1, no short, price limits)
  - GlobalEquityEngine: US / HK equities
  - CryptoEngine: Crypto perpetuals (funding fees, liquidation)
  - options_portfolio: European/American options (Black-Scholes, v2 with IV smile)

Wave 2:
  - FuturesBaseEngine: intermediate layer adding contract-multiplier logic
  - ChinaFuturesEngine: China commodity/financial futures (CFFEX/SHFE/DCE/ZCE/INE)
  - GlobalFuturesEngine: International futures (CME/ICE/Eurex)
  - ForexEngine: FX spot/CFD (spread, swap, high leverage)

Wave 3:
  - CompositeEngine: Cross-market engine with shared capital pool
  - _market_hooks: Extracted on_bar logic (funding, liquidation, swap)

Inheritance:
  BaseEngine
  ├── ChinaAEngine
  ├── GlobalEquityEngine
  ├── CryptoEngine
  ├── ForexEngine
  ├── CompositeEngine (delegates to sub-engines as rule providers)
  └── FuturesBaseEngine
      ├── ChinaFuturesEngine
      └── GlobalFuturesEngine
"""
