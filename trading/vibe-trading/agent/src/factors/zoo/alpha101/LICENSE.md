# Kakushadze 101 Formulaic Alphas — License & Provenance

## Display Name

**Kakushadze 101 Formulaic Alphas**

This is the display name used throughout the Vibe-Trading codebase, manifests,
wiki, and documentation when referring to the 101 alphas implemented under
`agent/src/factors/zoo/alpha101/`. No other branding is used.

## Source

* **Paper**: Z. Kakushadze, *"101 Formulaic Alphas"*, 2015.
* **arXiv**: <https://arxiv.org/abs/1601.00991>
* **DOI**: 10.48550/arXiv.1601.00991
* **License of the paper**: arXiv non-exclusive distribution license; the
  formulas themselves are presented as mathematical artifacts.

## What we reproduce

This subdirectory contains 101 standalone Python modules, one per alpha,
each implementing the formula given in the appendix of Kakushadze (2015) on
top of the operator surface in `agent/src/factors/base.py`. The
implementations were written from scratch against the formula table; we
did not copy or port source code from any third-party implementation.

## What we do NOT reproduce

* No prose, figures, tables, or discussion from the paper is included in
  this repository.
* No commentary on alpha behaviour, holding periods, or empirical
  performance is reproduced verbatim.
* The string commonly associated with the firm of one of the paper's
  author affiliations **does not appear anywhere in this repository**;
  the CI gate `tools/ci_grep_gates.sh` enforces this.

## Trademark / Naming Stance

Mathematical formulas are not subject to copyright. The formulas as listed
in the paper appendix are facts about real-valued functions of OHLCV data
and are reproducible by anyone with access to the paper. The choice of
display name **"Kakushadze 101 Formulaic Alphas"** credits the paper
author and avoids any trademark that may be associated with the
institutional affiliation of the work.

If you redistribute this subdirectory, please:

1. Keep the arXiv citation intact in each module docstring.
2. Keep the display name as **"Kakushadze 101 Formulaic Alphas"**.
3. Do not introduce trademark strings that this project deliberately
   avoids (see CI gate `(b)` in `tools/ci_grep_gates.sh`).

## Numerical Cross-Validation

Public reference implementations of these formulas exist (for example
Menooker/KunQuant on GitHub). We used those only as a numerical sanity
check on small synthetic panels — never as a source of code. No file in
this subdirectory was copied, adapted, or text-spliced from a third-party
implementation; the Python code here is original and was generated from
the formula table by a deterministic templating step (the template
generator script is not retained in the published source tree).

## Implementation Notes

* The standard panel exposes `open`, `high`, `low`, `close`, `volume`,
  `vwap`, and (optionally) `amount` and `sector`. Where the paper formula
  references `cap` (market capitalisation) or `IndClass.industry /
  subindustry / sector`, we either substitute a degraded value or gate
  the alpha behind `requires_sector=True`; the per-alpha `notes` field
  in `__alpha_meta__` records each such degradation.
* `delta(x, d)` is restricted to `d >= 1` (no negative-shift forms). The
  paper's formulas use only positive lags so this is a no-op constraint.
* The `delay(x, n)` helper (`x.shift(n)` with `n >= 1`) is implemented
  inside each alpha module as a small private function rather than
  imported from `src.factors.base` to keep the public operator surface
  small.

## Contact

Vibe-Trading project — <https://github.com/HKUDS/Vibe-Trading>
