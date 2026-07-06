## get_options_chain (agent tool)

----

Tool: `get_options_chain`
Backed by: `backtest.loaders.yahoo_client.get_options`
Description: Read-only agent/CLI tool that returns the US-listed options ladder
(calls and puts) for a single expiration, plus the list of available
expirations. Use it for an options snapshot — strike, bid/ask, last price,
volume, open interest, implied volatility, and the in/out-of-money flag. For
raw chain payloads call `yahoo_client.get_options` directly.

Each side is capped at 60 contracts so a deep chain cannot blow up the model
payload.

<br>
<br>

**Input parameters**

Name | Type | Required | Description
---- | ---- | -------- | -----------
ticker | str | Y | US underlying, `AAPL` or `AAPL.US` (the `.US` suffix is stripped).
expiration | int | N | Expiration as Unix epoch seconds (a value from the returned `expirations`). Omit for the nearest expiration.

<br>
<br>

**Output**

A JSON-string envelope.

On success:

```json
{"ok": true, "market": "us", "source": "yahoo", "data": {...}}
```

`data` fields:

Field | Type | Description
----- | ---- | -----------
ticker | str | Echoed input ticker.
expiration | int | The returned expiration as Unix epoch seconds.
expirations | list[int] | All available expirations as Unix epoch seconds.
calls_count | int | Number of call rows returned (≤ 60).
puts_count | int | Number of put rows returned (≤ 60).
calls | list[dict] | Call contracts (see fields below).
puts | list[dict] | Put contracts (same shape).

Per-contract fields (snake_case): `contract_symbol`, `strike`, `last_price`,
`bid`, `ask`, `volume`, `open_interest`, `implied_volatility`, `in_the_money`,
`expiration`.

On failure:

```json
{"ok": false, "error": "<message>"}
```

Failures are returned as an envelope (never raised) — e.g. a missing/blank
`ticker`, a non-integer `expiration`, or an upstream Yahoo request error.

<br>
<br>

**Example**

```text
get_options_chain(ticker="AAPL")
get_options_chain(ticker="AAPL.US", expiration=1718236800)
```

<br>
<br>

**Data example**

```json
{
  "ok": true, "market": "us", "source": "yahoo",
  "data": {
    "ticker": "AAPL",
    "expiration": 1718236800,
    "expirations": [1718236800, 1718841600],
    "calls_count": 2, "puts_count": 2,
    "calls": [{"contract_symbol": "AAPL240613C00190000", "strike": 190.0,
               "last_price": 4.05, "bid": 3.95, "ask": 4.10, "volume": 1203,
               "open_interest": 8821, "implied_volatility": 0.224,
               "in_the_money": true, "expiration": 1718236800}],
    "puts": [{"contract_symbol": "AAPL240613P00190000", "strike": 190.0,
              "last_price": 1.85, "bid": 1.80, "ask": 1.90, "volume": 642,
              "open_interest": 5104, "implied_volatility": 0.231,
              "in_the_money": false, "expiration": 1718236800}]
  }
}
```
