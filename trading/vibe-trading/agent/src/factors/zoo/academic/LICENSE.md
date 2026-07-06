# Academic Baseline Factors — Attributions and Stance

This subdirectory contains price-based proxies for the canonical academic
factor portfolios used as long-short benchmarks in the empirical
asset-pricing literature. None of the original papers' prose is reproduced
here.

## Source attributions

- Sharpe, W. F. (1964). "Capital Asset Prices: A Theory of Market
  Equilibrium under Conditions of Risk." *The Journal of Finance*,
  19(3), 425-442. — market factor (MKT-RF).
- Fama, E. F., & French, K. R. (1993). "Common risk factors in the
  returns on stocks and bonds." *Journal of Financial Economics*,
  33(1), 3-56. — SMB (size) and HML (value).
- Carhart, M. M. (1997). "On persistence in mutual fund performance."
  *The Journal of Finance*, 52(1), 57-82. — UMD (momentum).
- Fama, E. F., & French, K. R. (2015). "A five-factor asset pricing
  model." *Journal of Financial Economics*, 116(1), 1-22. — RMW
  (profitability) and CMA (investment).
- Hou, K., Xue, C., & Zhang, L. (2015). "Digesting anomalies: An
  investment approach." *Review of Financial Studies*, 28(3), 650-705.
  — Q-factor model (referenced for completeness; not implemented
  separately because the investment and profitability legs overlap
  with RMW / CMA in our OHLCV-only setting).

## Disclosure: these are price-based proxies, not the original factors

The implementations in this directory use only OHLCV panel inputs.
The original factor portfolios use fundamental data (book equity,
operating profitability, asset growth) that we do not carry in the
panel. We therefore replace each fundamental input with a price- or
volume-derived proxy:

- MKT-RF: 21-day per-stock total return (vs. value-weighted excess
  market return in the original).
- SMB: negative log of 60-day average dollar volume (vs. market
  capitalization in the original).
- HML: negative 252-day return (vs. book-to-market sort in the
  original).
- RMW: negative 60-day return volatility (vs. operating profitability
  sort in the original).
- CMA: negative 60-day change in log average volume (vs. asset-growth
  sort in the original).
- Carhart UMD: 12-month minus 1-month return (matches the original
  construction; cross-sectional z-score added for ranking).

Each module's `notes` field repeats this disclosure inline. Users
backtesting these factors as research-grade replacements for the
published series should obtain the authoritative monthly return series
from Kenneth French's data library:

  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

We link to that resource and do not copy any of its data files.

## Stance on factor definitions

Factor definitions are mathematical / academic concepts and are not
copyrightable. We re-state each factor as a cross-sectional ranking
signal in our own words and our own code. None of the original papers'
prose, tables, or figures is reproduced. The Kenneth French data
library's return series are owned by their authors and remain
externally hosted.
