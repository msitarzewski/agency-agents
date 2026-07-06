# qlib158 zoo — license & attribution

This subpackage (`agent/src/factors/zoo/qlib158/`) is a clean-room re-expression
of the **Alpha158** feature set defined by Microsoft's
[`qlib`](https://github.com/microsoft/qlib) project. Specifically, the field
catalogue and per-window combinations were taken from:

- **Upstream repo:** https://github.com/microsoft/qlib
- **Upstream license:** Apache License, Version 2.0
- **Pinned commit:** `d5379c520f66a39953bad76234a7019a72796fd0`
- **Pinned path:** `qlib/contrib/data/handler.py` (class `Alpha158`) and
  `qlib/contrib/data/loader.py` (class `Alpha158DL`)

Per-file headers in every `*.py` in this directory cite the same commit and
path, e.g.:

```
# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
```

## Scope of attribution

Apache-2.0 §4 requires us to (a) provide a copy of the License (the upstream
`LICENSE` is published at
<https://github.com/microsoft/qlib/blob/main/LICENSE>), (b) note prominently
that we modified the files, and (c) retain copyright / patent / trademark /
attribution notices from the source. The headers above satisfy (b) and (c);
this `LICENSE.md` plus the sibling `NOTICE` satisfy (a) and §4(d).

## What is "the work"?

The mathematical formulas for individual alpha features (e.g. `KMID = (close
- open) / open`, `MA5 = mean(close, 5) / close`) are facts of arithmetic and
not themselves subject to copyright. What we adapt from `qlib` is the
**curated catalogue**: the choice of which 9 K-bar features + 29 rolling
features × 5 windows to bundle together as "Alpha158", and the canonical
short names (KMID, KLEN, ROC, MA, …). That curation is the creative
contribution, and we attribute it accordingly.

The Python implementations in this directory are **re-written from scratch**
on top of `src.factors.base` operators — they do not copy any source code
from `qlib`. Differences from the upstream:

- We use a wide-DataFrame panel (`index=date, columns=instrument`) rather
  than `qlib`'s long-format expression tree.
- We compute on a `dict[str, pd.DataFrame]` panel passed to a pure
  `compute(panel)` function; no expression compiler, no caching layer.
- Division is routed through `safe_div` (epsilon-guarded, never silent inf).
- Look-ahead is forbidden at the operator level (`delta(d)` requires
  `d >= 1`); we do not expose `Ref(_, -n)`.

## Intentionally skipped fields

`Alpha158` in upstream `qlib` also includes 4 plain price reference features
(`OPEN`, `HIGH`, `LOW`, `VWAP` at window 0) that are *not* alpha signals —
they are raw inputs duplicated for downstream feature engineering. We do
not port them because (i) they would conflict with the wide-DataFrame panel
contract (output shape == close shape, raw price is already in `panel`), and
(ii) they offer no signal beyond the inputs. This brings the count to
9 + 29×5 = **154 alphas**.

No other Alpha158 field is skipped.

## Coverage summary

| Family   | Count | Stems |
|----------|-------|-------|
| K-bar    | 9     | kmid, klen, kmid2, kup, kup2, klow, klow2, ksft, ksft2 |
| Rolling  | 145   | (roc, ma, std, beta, rsqr, resi, max, min, qtlu, qtld, rank, rsv, imax, imin, imxd, corr, cord, cntp, cntn, cntd, sump, sumn, sumd, vma, vstd, wvma, vsump, vsumn, vsumd) × {5, 10, 20, 30, 60} |
| Skipped  | 4     | OPEN/HIGH/LOW/VWAP (price reference inputs, see above) |
| **Total**| **154** | |
