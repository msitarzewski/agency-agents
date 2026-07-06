## yahoo_client.search

----

Interface: `backtest.loaders.yahoo_client.search`
Endpoint: `GET https://query2.finance.yahoo.com/v1/finance/search`
Description: Resolve a free-text query (ticker fragment or company name) to
matching Yahoo instruments. Useful for symbol discovery before calling
`get_chart`, `get_quote_summary`, or `get_options`.

Auth: none (unauthenticated public endpoint). Routed through the shared
throttle because Yahoo rate-limits by source IP.

<br>
<br>

**Input parameters**

Name | Type | Required | Description
---- | ---- | -------- | -----------
query | str | Y | Free-text query — a ticker fragment (`AAPL`) or company name (`Apple`), sent as the `q` query param.

<br>
<br>

**Output**

Returns the `quotes` list (non-dict entries filtered out), or `[]` when nothing
matches. Each quote dict typically carries:

Field | Type | Description
----- | ---- | -----------
symbol | str | Yahoo ticker (use as-is for the other client calls, or map back to project form).
shortname | str | Short instrument name.
longname | str | Full instrument name (when available).
exchange | str | Exchange code.
quoteType | str | Instrument type (`EQUITY`, `ETF`, `INDEX`, `CRYPTOCURRENCY`, ...).

Raises `requests.RequestException` on a network/HTTP failure.

<br>
<br>

**Example**

```python
from backtest.loaders import yahoo_client

matches = yahoo_client.search("Apple")
for quote in matches[:3]:
    print(quote.get("symbol"), quote.get("shortname"), quote.get("quoteType"))
```

<br>
<br>

**Data example**

```text
AAPL    Apple Inc.              EQUITY
APLE    Apple Hospitality REIT  EQUITY
AAPL.MX Apple Inc.              EQUITY
```
