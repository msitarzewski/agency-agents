## yahoo_client.get_quote_summary

----

Interface: `backtest.loaders.yahoo_client.get_quote_summary`
Endpoint: `GET https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}`
Description: Fetch one or more Yahoo quoteSummary **modules** for a symbol —
valuation key statistics, analyst financials/estimates, ownership, and similar
fundamentals. This is the data source behind the `get_stock_profile` tool; call
the tool when you want a compact, projected envelope, and call this function
directly when you need raw module payloads or a module the tool does not expose.

Auth: the v10 quoteSummary endpoint requires a session **cookie** plus a
matching **crumb** token. The client performs this handshake lazily on first
use and refreshes it once on a `401` (the documented "crumb expired /
unauthorized" signal), so callers never manage cookies or crumbs. All requests
route through the shared throttle because Yahoo rate-limits by source IP.

<br>
<br>

**Input parameters**

Name | Type | Required | Description
---- | ---- | -------- | -----------
symbol | str | Y | Project-side symbol (`AAPL.US`, `00700.HK`). Mapped to Yahoo form via `map_symbol`.
modules | list[str] | Y | Yahoo module names to request, joined as the `modules` query param.

Commonly used module names:

Module | Contents
------ | --------
price | Current price, exchange, currency, market state.
summaryDetail | Day range, 52-week range, volume, dividend yield, market cap.
defaultKeyStatistics | Enterprise value, forward PE, EPS, PEG, price-to-book, shares outstanding, insider/institution held %.
financialData | Current price, analyst target prices, recommendation key, revenue/margins, cash/debt, ROE.
earningsTrend | Per-period EPS and revenue estimates with growth and analyst counts.
institutionOwnership | Top institutional holders (organization, report date, pct held, position, value).
insiderHolders | Insider holders (name, relation, latest transaction date, position).
recommendationTrend | Strong-buy / buy / hold / sell / strong-sell counts per period.
assetProfile | Sector, industry, business summary, officers, employee count.

<br>
<br>

**Output**

Returns the `quoteSummary.result[0]` mapping: a dict keyed by the requested
module names, each value the verbose Yahoo module payload. Returns `{}` when
Yahoo returns no result for the symbol.

Many scalar cells arrive as Yahoo `{"raw": <number>, "fmt": <string>}` wrappers
— take the `raw` member for the numeric value (the `get_stock_profile` tool's
`_raw` helper does exactly this).

Raises `requests.RequestException` on a non-401 HTTP failure or a second
consecutive `401`, and `ValueError` when Yahoo reports a per-symbol error.

<br>
<br>

**Example**

```python
from backtest.loaders.yahoo_client import get_quote_summary

summary = get_quote_summary("AAPL.US", ["price", "defaultKeyStatistics"])
price = summary.get("price", {})
stats = summary.get("defaultKeyStatistics", {})
print(price.get("regularMarketPrice", {}).get("raw"))
print(stats.get("forwardPE", {}).get("raw"))
```

<br>
<br>

**Data example**

```text
{
  "price": {"regularMarketPrice": {"raw": 192.2, "fmt": "192.20"}, "currency": "USD"},
  "defaultKeyStatistics": {"forwardPE": {"raw": 27.4, "fmt": "27.40"},
                            "priceToBook": {"raw": 45.1, "fmt": "45.10"}}
}
```
