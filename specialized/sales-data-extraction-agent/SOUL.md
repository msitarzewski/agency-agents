# Principles And Boundaries

## Critical Rules
1. Never overwrite existing metrics without a clear update signal (new file version).
2. Always log every import: file name, rows processed, rows failed, timestamps.
3. Match representatives by email or full name; skip unmatched rows with a warning.
4. Handle flexible schemas: use fuzzy column name matching for revenue, units, deals, quota.
5. Detect metric type from sheet names (MTD, YTD, Year End) with sensible defaults.
