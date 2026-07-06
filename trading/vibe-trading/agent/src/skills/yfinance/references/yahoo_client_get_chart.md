## yahoo_client.get_chart

----

Interface: `backtest.loaders.yahoo_client.get_chart`
Endpoint: `GET https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`
Description: Fetch OHLCV bars directly from Yahoo's v8 chart endpoint as
ascending row dicts. This is the lowest-level price call — for normal backtest
or agent OHLCV work prefer the `get_market_data` tool or the yfinance loader,
which already routes through this client and normalizes the frame. Use
`get_chart` directly only when you need raw bars with a custom interval/window
and want to map them yourself.

Auth: none (unauthenticated public endpoint). All traffic passes through the
shared throttle (`backtest.loaders._http`) because Yahoo rate-limits by source
IP; spacing is enforced process-wide across every Yahoo call.

<br>
<br>

**Input parameters**

Name | Type | Required | Description
---- | ---- | -------- | -----------
symbol | str | Y | Project-side symbol (`AAPL.US`, `00700.HK`, `BTC-USD`, `^GSPC`). Mapped to Yahoo form via `map_symbol`.
interval | str | N | Bar size accepted by Yahoo: `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`. Default `1d`.
period1 | int | N | Inclusive start as Unix epoch seconds. Ignored when `range_` is given.
period2 | int | N | Exclusive end as Unix epoch seconds. Ignored when `range_` is given.
range_ | str | N | Relative range string (`1d`, `5d`, `1mo`, `6mo`, `1y`, `5y`, `max`). Takes precedence over `period1`/`period2` when both are supplied.

Supply either `range_` or a `period1`/`period2` window. Minute-bar history is
limited by Yahoo (1m ≈ 7 days; 2m–90m ≈ 60 days; 1h ≈ 730 days; daily+ is
unbounded).

<br>
<br>

**Output**

Returns a `list[dict]` of ascending bars. Each row:

Field | Type | Description
----- | ---- | -----------
trade_date | int | Bar timestamp as Unix epoch seconds.
open | float | Open price.
high | float | High price.
low | float | Low price.
close | float | Close price.
volume | float | Traded volume.

Bars whose OHLC is `null` (non-trading slots Yahoo pads in) are dropped. An
empty list is returned when Yahoo reports no data for the symbol/window.

Raises `requests.RequestException` on a network/HTTP failure and `ValueError`
when Yahoo reports a per-symbol error or the payload is structurally unusable.

<br>
<br>

**Example**

```python
from backtest.loaders import yahoo_client

# Relative range
bars = yahoo_client.get_chart("AAPL.US", interval="1d", range_="1mo")

# Explicit epoch window
import time
end = int(time.time())
start = end - 7 * 24 * 3600
intraday = yahoo_client.get_chart(
    "AAPL.US", interval="5m", period1=start, period2=end
)
for row in bars[:3]:
    print(row)
```

<br>
<br>

**Data example**

```text
{'trade_date': 1717075800, 'open': 191.5, 'high': 192.6, 'low': 190.9, 'close': 192.2, 'volume': 48211000.0}
{'trade_date': 1717162200, 'open': 192.9, 'high': 194.0, 'low': 192.1, 'close': 193.5, 'volume': 51122300.0}
```
