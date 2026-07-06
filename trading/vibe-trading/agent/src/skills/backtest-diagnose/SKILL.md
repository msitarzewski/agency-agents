---
name: backtest-diagnose
description: Diagnose failed or underperforming backtests, locate the root cause, and fix the issue
category: tool
---

# Backtest Diagnosis

## Overview

Use this skill when a user reports that a backtest failed, raised an error, or produced poor results.

## Diagnostic Workflow

1. **Read existing artifacts**: use `read_file` to inspect `artifacts/metrics.csv`, `equity.csv`, and `trades.csv`
2. **Read the code**: use `read_file` to inspect `code/signal_engine.py` and `config.json`
3. **Classify the issue**: determine the root cause using the error taxonomy below
4. **Apply the fix**: use `edit_file` to modify the code, then rerun the backtest
5. **Verify the fix**: use `read_file` to inspect the new `metrics.csv`

## Error Taxonomy

### Runtime Errors (`exit_code != 0`)

| Error Type | Common Cause | Fix |
|---------|---------|---------|
| ImportError | Missing dependency | `bash("pip install xxx")` |
| KeyError | DataFrame column-name mismatch | Check the actual column names in `data_map` |
| IndexError | Empty data or insufficient length | Add length checks |
| TypeError | Incorrect signal type | Ensure the return value is `pd.Series` |

### Logic Bugs (Backtest Succeeds but Results Are Abnormal)

1. **Zero trades** (`trade_count=0`): signal-logic bug. Conditions are too strict, so the signal stays at 0. Check whether entry and exit logic is reasonable, and inspect the signal series to confirm it is not all zeros.
2. **Late trades** (first trade occurs more than 2 years after the backtest start): data-filtering bug. The lookback window may be too long, or the initial data segment may have been dropped. Shorten the window or check whether `dropna` is too aggressive.
3. **Capital utilization < 50%** (mostly in cash): position-sizing bug. Signal triggers may be too sparse, or the position-sizing logic may be wrong.
4. **Open position at the end** (a position still exists when the backtest ends): exit-timing bug. Forced liquidation may be missing, or exit logic does not cover the final segment.

### Data Errors

| Symptom | Root Cause | Fix |
|------|------|---------|
| No data fetched | Invalid API token or code issue | Check `config.json` |
| Too little data | Date range too narrow | Expand the date range |

### Data-Source Error Ignore List

If you encounter the following keywords, **do not modify the code**. The problem is on the data-provider side:
- a provider-side "no data available" response
- `rate limit`
- `API limit`
- `daily limit`
- `Information` (common in Tushare API responses)

These issues require the user to check the API token, switch data sources, or wait for the quota to reset.

## Hard-Gate Checklist

1. `artifacts/metrics.csv` exists and is non-empty
2. `artifacts/equity.csv` exists and is non-empty
3. `trade_count > 0` (`0` trades means a signal bug)
4. The equity series contains no `NaN`
5. `exit_code == 0`

## Fixing Principles

- Use **edit_file** to make precise code fixes instead of rewriting the entire file with `write_file`, unless the structure is fundamentally broken
- Fix the bug only, do not change strategy logic unless the user explicitly asks
- Fix one issue at a time, and rerun the backtest immediately after each fix
- Limit yourself to at most 3 repair iterations

## Post-Fix Validation Rules

After modifying `signal_engine.py`, you must confirm:
1. **AST syntax passes**: `bash("python -c \"import ast; ast.parse(open('code/signal_engine.py').read()); print('OK')\"")`
2. **Contains `class SignalEngine`**: the file must define `class SignalEngine`
3. **Contains `def generate`**: the class must contain a `def generate` method
4. **Rerun the backtest**: after the fix, rerun the backtest and verify the results

## `action_items` Writing Rules

After diagnosis, output actionable improvement suggestions:
- Format: `"Change X from A to B"` or `"Add X logic in signal_engine.py"`
- Be specific about parameter values, filenames, and function names
- Provide at least 2 items
- Examples:
  - `"Change RSI threshold from 30 to 25 in signal_engine.py line 42"`
  - `"Add signals = signals.fillna(0) after signal calculation to prevent NaN propagation"`
  - `"Add a volume filter: skip buy signals when volume is below the 20-day average"`
