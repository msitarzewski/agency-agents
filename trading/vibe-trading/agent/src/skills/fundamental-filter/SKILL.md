---
name: fundamental-filter
description: Fundamental factor screening — filter stocks by PE/PB/ROE, financial statement fields, and other metrics for value or growth selection. Supports A-shares (via tushare extra_fields or fundamental_fields) and HK/US stocks (via yfinance Ticker info).
category: flow
---
# Fundamental Factor Screening

## Purpose

Filter stocks using fundamental financial data (PE/PB/ROE, etc.) to build value or growth screen signals for backtesting. Supports multiple markets with different data sources.

## Market Support

| Market | Data Source | Method | Supported Metrics |
|--------|-----------|--------|------------------|
| A-shares | tushare `daily_basic` | `extra_fields` in config.json | pe, pb, pe_ttm, ps_ttm, dv_ttm, total_mv, circ_mv, roe |
| A-shares | Tushare statements | `fundamental_fields` in config.json | income, balancesheet, cashflow, fina_indicator fields |
| US stocks | yfinance `Ticker.info` | Direct API call | trailingPE, forwardPE, priceToBook, returnOnEquity, marketCap, dividendYield |
| HK stocks | yfinance `Ticker.info` | Direct API call | trailingPE, priceToBook, returnOnEquity, marketCap |

## Signal Logic

### Value Filter (Default)

1. PE < pe_max AND PE > 0 (exclude loss-making stocks)
2. PB < pb_max
3. ROE > roe_min
4. All conditions met → long (1), otherwise → flat (0)

### Growth Filter (Optional)

1. PE_TTM within reasonable range (0 < PE_TTM < pe_ttm_max)
2. ROE > roe_min (profitability floor)
3. Market cap > mv_min (exclude micro-caps)

## A-Share Usage (tushare)

### config.json

```json
{
  "source": "tushare",
  "codes": ["000001.SZ", "600036.SH", "000858.SZ"],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "extra_fields": ["pe", "pb", "pe_ttm", "roe", "total_mv"],
  "initial_cash": 1000000,
  "commission": 0.001
}
```

The `extra_fields` columns are automatically merged into the daily DataFrame by the DataLoader.

### A-Share Statement Pre-Filter

Use `fundamental_fields` when the strategy needs PIT-safe financial statement data instead of daily valuation fields:

```json
{
  "source": "tushare",
  "codes": ["000001.SZ", "600036.SH", "000858.SZ"],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "fundamental_fields": {
    "income": ["total_revenue", "n_income"],
    "balancesheet": ["total_hldr_eqy_exc_min_int"],
    "fina_indicator": ["roe", "debt_to_assets"]
  },
  "initial_cash": 1000000,
  "commission": 0.001
}
```

The backtest runner queries the configured tables through `TushareFundamentalProvider` and merges each published statement snapshot into daily bars only after its announcement/disclosure date. Statement columns are prefixed by table name:

| Requested field | SignalEngine column |
|-----------------|---------------------|
| `income.total_revenue` | `income_total_revenue` |
| `income.n_income` | `income_n_income` |
| `balancesheet.total_hldr_eqy_exc_min_int` | `balancesheet_total_hldr_eqy_exc_min_int` |
| `fina_indicator.roe` | `fina_indicator_roe` |

Representative financial-quality pre-filter:

```python
revenue = row.get("income_total_revenue")
profit = row.get("income_n_income")
net_assets = row.get("balancesheet_total_hldr_eqy_exc_min_int")
roe = row.get("fina_indicator_roe")

passes = (
    revenue is not None and revenue > 0
    and profit is not None and profit > 0
    and net_assets is not None and net_assets > 0
    and roe is not None and roe >= 8.0
)
```

## HK/US Stock Usage (yfinance)

For HK/US stocks, fundamental data is not available as daily time-series via the backtest loader. Instead, use `yfinance` Ticker info for point-in-time screening:

```python
import yfinance as yf

def screen_us_stocks(tickers, criteria):
    """Screen US/HK stocks by fundamental criteria."""
    passed = []
    for symbol in tickers:
        info = yf.Ticker(symbol).info
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity")  # Decimal (e.g., 0.25 = 25%)
        mcap = info.get("marketCap")

        if pe is None or pb is None or roe is None:
            continue  # Skip stocks with missing data

        if (0 < pe < criteria["pe_max"]
            and pb < criteria["pb_max"]
            and roe > criteria["roe_min"]
            and (mcap or 0) > criteria.get("mcap_min", 0)):
            passed.append({
                "symbol": symbol,
                "pe": pe,
                "pb": pb,
                "roe": round(roe * 100, 1),  # Convert to percentage
                "mcap": mcap,
            })

    return passed

# Example: screen S&P 500 components
criteria = {"pe_max": 20, "pb_max": 3.0, "roe_min": 0.08, "mcap_min": 10_000_000_000}
results = screen_us_stocks(["AAPL", "MSFT", "JNJ", "JPM", "XOM"], criteria)
```

### HK Stock Screening

```python
# HK stocks use the same yfinance interface
hk_tickers = ["0700.HK", "9988.HK", "1810.HK", "2318.HK", "0005.HK"]
results = screen_us_stocks(hk_tickers, criteria)  # Same function works
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| pe_max | 20.0 | PE ceiling (exclude overvalued) |
| pb_max | 3.0 | PB ceiling |
| roe_min | 8.0 | ROE floor (%), exclude low-profitability |
| pe_min | 0.0 | PE floor (exclude loss-making stocks) |
| mcap_min | 0 | Market cap floor (for US/HK, in USD) |

## Common Pitfalls

- `extra_fields` columns may contain NaN (new listings, ST stocks) — must `fillna` or `dropna`
- `fundamental_fields` columns are prefixed by table and may be NaN before the first statement is published in the backtest window
- Do not forward-fill statement rows manually before their `ann_date` / `f_ann_date`; the runner's merge already enforces point-in-time visibility
- Negative PE means loss-making — always filter with `pe > 0`
- ROE units differ: tushare uses percentage (e.g., 15 = 15%), yfinance uses decimal (e.g., 0.15 = 15%)
- For portfolio strategies: N stocks passing the screen each get weight 1/N
- yfinance `Ticker.info` is a point-in-time snapshot, not historical time-series — cannot directly use for daily rebalancing backtests on US/HK stocks
- For US/HK daily fundamental backtests, consider using the screening results as a stock universe, then applying technical signals within that universe

## Dependencies

```bash
pip install pandas numpy yfinance
```

## Signal Convention

- `1/N` = selected for long (N = number of stocks passing the screen), `0` = not selected
