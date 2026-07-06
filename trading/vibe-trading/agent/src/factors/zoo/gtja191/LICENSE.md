# GTJA Alpha 191 — Provenance and Licensing Note

**Display name:** GTJA Alpha 191

## Source

国泰君安证券 (Guotai Junan Securities) 2014 research report
*"191 个短周期交易型 alpha 因子" — 191 Short-Period Transactional Alpha Factors*.
The report is part of Guotai Junan's published Chinese-A-share quantitative research series
and was distributed publicly through the firm's research portal and partner channels.

## Authors

The report is attributed to the Guotai Junan quantitative research team. Where
individual author names appear on the cover page (光辉 / Guang Hui and 彭祖虎 /
Peng Zuhu in some circulating copies), they are credited to the original work;
this repository does not claim derived authorship of the formulas themselves.

## Year

2014.

## What is reproduced here

This directory contains only the **mathematical alpha formulas** (the 191
short-period alpha definitions, numbered 1–191) re-expressed in this project's
operator algebra (`src.factors.base`). The report's narrative prose, worked
examples, in-sample / out-of-sample performance tables, figures, and any
proprietary commentary are **not reproduced** in this repository.

The formulas themselves are factual mathematical content: a recipe expressed in
algebra and time-series operators. We take the position that such factual
mathematical expressions are not subject to copyright in the same way as
expressive prose, and the report's narrative material (which would be
expressive) is deliberately omitted from this repo.

We do not invoke any US affirmative-defense doctrine to justify this
reproduction. The position is simpler: only the formulas (factual
mathematics) are reproduced; the report's prose, framing, and figures are not.

## Reference implementations consulted

Several open-source GitHub re-implementations of the 191 formulas exist (in
Python with pandas/numpy, or in proprietary DSLs such as Tushare-Pro's
`Alpha101_191` examples). They were used **only for numerical cross-checks** on
a small sample of alphas to catch transcription errors against the published
formulas — **no source code was copied** from any of those projects into this
repository. The operator vocabulary used here (`rank`, `ts_corr`, `decay_linear`,
`signed_power`, `safe_div`, …) is this project's own and is defined in
`src.factors.base`.

## Operator-availability deviations

A small number of alphas required interpretation choices because the original
formulas use primitives that have no exact 1:1 mapping in `src.factors.base`.
In every such case, we picked the closest semantically faithful alternative
**and documented the choice in the alpha's `__alpha_meta__["notes"]` field**.
The most common substitutions:

- `WMA(x, n)` — the original report uses a specific weighted moving average with
  weights `0.9, 0.9², …`. We approximate with `decay_linear(x, n)` (linearly
  decaying weights), noted in affected alphas (e.g. gtja191_009, gtja191_039,
  gtja191_047).
- `SMA(x, n, m)` — Wilder-style EMA with explicit `m/n` smoothing — mapped to
  `x.ewm(alpha=m/n, adjust=False).mean()` (pandas), documented per-alpha when
  used.
- `REGBETA(x, y, n)` and `REGRESI(x, y, n)` — rolling OLS slope and residual
  are approximated as `ts_cov(x, y, n) / ts_std(y, n) ** 2` (slope) and
  `x - beta * y` (residual). Affected alphas note this explicitly.
- `FILTER(x, cond)` — implemented as `x.where(cond, np.nan)` so unmet rows
  propagate NaN rather than silently zero-fill.
- `SUMIF(x, cond, n)` — implemented as `(x * cond).rolling(n).sum()` with
  boolean → float coercion documented where it appears.
- `HIGHDAY` / `LOWDAY` use `ts_argmax` / `ts_argmin` with **0-based** positions
  inside the window (vs. the report's 1-based convention); a `(n - argmax)`-style
  re-base is applied where the formula's downstream arithmetic depends on the
  count rather than the index.

When a benchmark index series (`benchmark_close`) is referenced by the original
formula but unavailable in this panel, we fall back to the per-day
cross-sectional mean of `close`. The substitution is noted in
`__alpha_meta__["notes"]` of every affected alpha (gtja191_006-style market
betas and the handful of explicitly index-driven alphas).

## Look-ahead and purity contract

All ports comply with the repository-wide ports purity contract enforced by
`tests/factors/test_alpha_purity.py` (whitelist of imports, no I/O, no eval) and
the look-ahead guard in `tests/factors/test_lookahead.py` (no `Ref(x, -n)`,
`delta(d >= 1)` only).

## Display name and citation

When citing this re-implementation, please reference:
- Guotai Junan Securities, "191 个短周期交易型 alpha 因子", 2014.
- The display name **"GTJA Alpha 191"** for the directory in this repository.
