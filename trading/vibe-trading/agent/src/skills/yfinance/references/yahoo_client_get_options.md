## yahoo_client.get_options

----

Interface: `backtest.loaders.yahoo_client.get_options`
Endpoint: `GET https://query2.finance.yahoo.com/v7/finance/options/{symbol}`
Description: Fetch the Yahoo v7 option chain for an underlying — the list of
available expirations plus the calls/puts ladder for one expiration. This is
the data source behind the `get_options_chain` tool; call the tool for a
capped, snake_case envelope, and call this function directly when you need the
raw chain (e.g. all contract fields, strikes array, or quote block).

Auth: none (unauthenticated public endpoint). Routed through the shared
throttle because Yahoo rate-limits by source IP.

<br>
<br>

**Input parameters**

Name | Type | Required | Description
---- | ---- | -------- | -----------
symbol | str | Y | Project-side underlying symbol (`AAPL.US`). Mapped to Yahoo form via `map_symbol`.
expiration | int | N | Expiration as Unix epoch seconds (one of `expirationDates`). Omit for the nearest expiration.

<br>
<br>

**Output**

Returns the `optionChain.result[0]` mapping, or `{}` when Yahoo has no chain.
Key members:

Field | Type | Description
----- | ---- | -----------
underlyingSymbol | str | The resolved Yahoo underlying ticker.
expirationDates | list[int] | All available expirations as Unix epoch seconds.
strikes | list[float] | All strike prices for the returned expiration.
options | list[dict] | One block for the chosen expiration with `expirationDate`, `calls`, `puts`.

Each entry in `calls` / `puts` is a contract dict with (among others)
`contractSymbol`, `strike`, `lastPrice`, `bid`, `ask`, `volume`,
`openInterest`, `impliedVolatility`, `inTheMoney`, and `expiration`.

Raises `requests.RequestException` on a network/HTTP failure and `ValueError`
when Yahoo reports a per-symbol error.

<br>
<br>

**Example**

```python
from backtest.loaders import yahoo_client

# Nearest expiration
chain = yahoo_client.get_options("AAPL.US")
expirations = chain.get("expirationDates", [])
block = (chain.get("options") or [{}])[0]
print(len(block.get("calls", [])), "calls")

# A specific later expiration
if len(expirations) > 1:
    later = yahoo_client.get_options("AAPL.US", expiration=expirations[1])
```

<br>
<br>

**Data example**

```text
{
  "underlyingSymbol": "AAPL",
  "expirationDates": [1718236800, 1718841600, 1719446400],
  "options": [{
    "expirationDate": 1718236800,
    "calls": [{"contractSymbol": "AAPL240613C00190000", "strike": 190.0,
               "lastPrice": 4.05, "bid": 3.95, "ask": 4.10, "volume": 1203,
               "openInterest": 8821, "impliedVolatility": 0.224,
               "inTheMoney": true}],
    "puts": [{"contractSymbol": "AAPL240613P00190000", "strike": 190.0,
              "lastPrice": 1.85, "bid": 1.80, "ask": 1.90, "volume": 642,
              "openInterest": 5104, "impliedVolatility": 0.231,
              "inTheMoney": false}]
  }]
}
```
