---
name: dividend-analysis
description: Dividend stock analysis for income, dividend-growth, and shareholder-return strategies, including yield quality, payout sustainability, ex-dividend mechanics, and yield-trap checks.
category: analysis
---

# Dividend Analysis

## Purpose

Use this skill when the user asks about dividend stocks, income portfolios, dividend growth, high-yield screening, payout safety, ex-dividend dates, or whether a dividend is sustainable. The goal is to separate durable shareholder returns from yield traps.

Dividend analysis should never stop at headline yield. A good answer explains how the dividend is funded, how stable the underlying business is, whether management has room to keep paying, and how valuation changes the expected total return.

## Core Questions

1. What is the current cash yield, and is it normal for this company or sector?
2. Is the payout covered by earnings, operating cash flow, and free cash flow?
3. Is the balance sheet strong enough to absorb a down cycle?
4. Has management grown, held, cut, or suspended the dividend across cycles?
5. Does the valuation still leave room for total return after taxes and reinvestment assumptions?

## Key Metrics

| Metric | Formula | Healthy Signal | Warning Signal |
|--------|---------|----------------|----------------|
| Dividend yield | annual DPS / current price | Above peer median with stable coverage | Extremely high vs history or peers |
| Earnings payout ratio | dividends / net income, or DPS / EPS | 30-70% for mature non-financials | Above 90%, negative earnings |
| Free-cash-flow payout | dividends / FCF | Below 70% through a cycle | Dividend exceeds FCF for 2+ years |
| CFO coverage | operating cash flow / dividends paid | Above 1.5x | Below 1.0x |
| Dividend CAGR | DPS growth over 3/5/10 years | Positive and below EPS/FCF growth | Growth funded by leverage |
| Net debt / EBITDA | net debt / EBITDA | Sector-appropriate leverage | Leverage rising while payout rises |
| Buyback plus dividend yield | (dividends + net buybacks) / market cap | Balanced capital return | Buybacks funded by debt at high valuation |

For REITs, utilities, banks, MLPs, and insurers, adapt the payout metric to the sector. For example, use AFFO payout for REITs, distributable cash flow for MLPs, and regulatory capital ratios for banks and insurers.

## Analysis Workflow

### Step 1: Normalize the Dividend

- Use forward indicated dividend for recurring payments.
- Separate ordinary dividends from special dividends.
- Check whether the latest declared dividend is annual, semiannual, quarterly, monthly, or irregular.
- For ADRs and cross-listed shares, account for depositary ratios, withholding tax, and FX conversion.

```python
annual_dividend = regular_dividend_per_period * payments_per_year
dividend_yield = annual_dividend / current_price
```

### Step 2: Check Coverage

Start with earnings coverage, then confirm with cash coverage.

```python
earnings_payout = dividends_paid / net_income
fcf_payout = dividends_paid / free_cash_flow
cfo_coverage = operating_cash_flow / dividends_paid
```

Interpretation:

- Good: net income, CFO, and FCF all cover dividends across multiple years.
- Watch: earnings cover dividends but FCF does not, especially during capex-heavy periods.
- Avoid: dividends are paid while both earnings and FCF are negative, unless there is a clear one-time reason and a strong balance sheet.

### Step 3: Diagnose Dividend Growth Quality

Dividend growth is high quality when it follows business growth.

```python
dividend_cagr = (dps_end / dps_start) ** (1 / years) - 1
eps_cagr = (eps_end / eps_start) ** (1 / years) - 1
fcf_cagr = (fcf_end / fcf_start) ** (1 / years) - 1
```

Quality rules:

- Dividend CAGR below EPS and FCF CAGR usually leaves room for future increases.
- Dividend CAGR above EPS/FCF CAGR means payout ratio is expanding.
- Flat dividend with rising FCF may imply hidden capacity or conservative management.
- Repeated small increases can still be fragile if leverage is rising.

### Step 4: Check Balance Sheet Flexibility

Look for the ability to maintain dividends during stress.

| Item | Why It Matters |
|------|----------------|
| Cash and short-term investments | Near-term cushion |
| Net debt / EBITDA | Debt burden against operating earnings |
| Interest coverage | Ability to service debt before shareholder returns |
| Debt maturity wall | Refinancing risk in high-rate environments |
| Credit rating or covenant language | External constraints on payout policy |

### Step 5: Separate Dividend Yield from Total Return

Dividend stocks can underperform if the yield comes from a falling price. Always connect income to valuation and growth.

```python
expected_total_return = dividend_yield + expected_eps_growth + valuation_rerating
```

Do not present this as a guarantee. Use it as a scenario framework.

## Yield-Trap Checklist

Flag a potential yield trap when several of these are true:

- Dividend yield is more than 2x the company's 5-year median or sector median.
- Payout ratio is above 90%, or FCF payout is above 100%.
- Revenue, EPS, or FCF has declined for 2+ years.
- Net debt / EBITDA is rising while interest coverage is falling.
- Management has recently issued equity or debt while maintaining dividends.
- The stock price fell before the yield became attractive.
- Dividend history includes cuts, suspensions, or frequent special dividends labeled as ordinary income.
- Sector faces structural pressure, regulation risk, or commodity down-cycle exposure.

## Strategy Types

### Dividend Growth

Prioritize moderate yield, strong dividend CAGR, low payout ratio, and durable business quality.

Good for users seeking compounding and lower cut risk.

### High-Yield Quality

Prioritize yield, but require cash coverage, balance sheet resilience, and sector-aware payout norms.

Good for users seeking current income, but the answer must discuss cut risk.

### Shareholder Yield

Combine dividends, net buybacks, and debt reduction.

Useful when companies return capital mostly through buybacks rather than cash dividends.

```python
shareholder_yield = dividend_yield + net_buyback_yield + debt_paydown_yield
```

### Dividend Capture

Buying before the ex-dividend date only to collect the dividend is not a free-money strategy. Prices usually adjust around the ex-dividend date, and taxes, spreads, and slippage can erase the gross dividend.

Use this only as an event-risk analysis, not as a default recommendation.

## Data Sources

| Market | Useful Fields |
|--------|---------------|
| A-shares | Tushare `dividend`, `daily_basic.dv_ttm`, `fina_indicator`, `cashflow` |
| US/HK | yfinance `Ticker.dividends`, `Ticker.info`, financial statements, cash flow |
| ETFs | distribution yield, SEC yield, holdings yield, expense ratio, distribution history |
| REITs | FFO, AFFO, occupancy, debt maturities, AFFO payout |

When live data is unavailable, state the limitation and provide the analysis template instead of inventing dividend figures.

## Output Template

```markdown
### Dividend Analysis: [ticker/company]

**Verdict:** [sustainable / watchlist / yield-trap risk]

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Dividend yield | ... | ... |
| Earnings payout | ... | ... |
| FCF payout | ... | ... |
| Dividend growth | ... | ... |
| Balance sheet | ... | ... |

**What supports the dividend**
- ...

**What could break the dividend**
- ...

**Scenario view**
- Base: ...
- Downside: ...
- Upside: ...

**Research note:** This is investment research, not live trading advice.
```

## Common Mistakes

- Treating high yield as cheap valuation without checking why the price fell.
- Mixing special dividends with regular dividends.
- Comparing REIT payout ratios to ordinary industrial companies.
- Ignoring withholding tax, ADR ratios, currency conversion, or ETF expense drag.
- Forgetting that ex-dividend capture is usually offset by price adjustment and transaction costs.
- Recommending a dividend stock without discussing total return and dividend-cut risk.
