# sec_edgar_client — SEC EDGAR transport

Module: `backtest.loaders.sec_edgar_client`

A thin, IP-throttled REST client over the SEC's free JSON endpoints. It returns raw decoded JSON for downstream loaders/tools to shape; it is **not** a `DataLoaderProtocol` implementation and is not registered as a backtest `source`. Use it directly only when you need data the `get_sec_filings` tool does not already surface.

## Public functions

### `cik_for(ticker: str) -> Optional[str]`

Resolve a U.S. ticker to its zero-padded 10-digit CIK.

- **Args**: `ticker` — a U.S. equity ticker, case-insensitive (`"AAPL"`, `"msft"`).
- **Returns**: the padded CIK string (`"0000320193"`), or `None` when the ticker is empty or absent from the SEC table.
- **Raises**: `requests.RequestException` if the one-time tickers fetch fails.

The ticker→CIK table is fetched once per process from `company_tickers.json` and memoized (thread-safe). Lookups after the first are in-memory.

```python
from backtest.loaders.sec_edgar_client import cik_for

cik = cik_for("AAPL")   # "0000320193"
missing = cik_for("NOT_A_TICKER")  # None
```

### `get_submissions(cik: str | int) -> Dict[str, Any]`

Fetch the filing-index ("submissions") document for a CIK.

- **Args**: `cik` — int or string; padded to 10 digits internally (a `"CIK"` prefix or leading zeros are tolerated).
- **Returns**: the decoded submissions document — company metadata plus the recent-filings block at `filings.recent` (parallel arrays: `form`, `accessionNumber`, `filingDate`, `reportDate`, `primaryDocument`, `primaryDocDescription`, ...).
- **Raises**: `ValueError` if `cik` contains no digits; `requests.RequestException` on a non-2xx status or undecodable body.

### `get_company_facts(cik: str | int) -> Dict[str, Any]`

Fetch the XBRL `companyfacts` document for a CIK.

- **Args**: `cik` — int or string; padded internally.
- **Returns**: the decoded companyfacts document. Concepts nest as `facts.us-gaap.<Concept>.units.<Unit>` → a list of points (`{end, val, fy, fp, form, accn, frame?}`).
- **Raises**: `ValueError` if `cik` contains no digits; `requests.RequestException` on a non-2xx status or undecodable body.

## CIK padding

The SEC's submissions and companyfacts endpoints key on the **zero-padded 10-digit** CIK. The client normalizes any input — int, padded string, or `"CIK"`-prefixed — by keeping the digits and left-zero-filling to width 10. Primary-document URLs, by contrast, use the **un-padded** CIK (leading zeros stripped).

| Input | Padded (endpoints) | Un-padded (doc URLs) |
|-------|--------------------|----------------------|
| `320193` | `0000320193` | `320193` |
| `"0000320193"` | `0000320193` | `320193` |
| `"CIK0000320193"` | `0000320193` | `320193` |

## Throttling & User-Agent

Every request goes through `backtest.loaders._http` under the `"sec"` host bucket, enforcing a per-request spacing floor of ~0.12s (well under the SEC's ~10 req/s ceiling). The client also sends a descriptive contact `User-Agent`, which the SEC fair-access policy requires; bursting without one earns a temporary IP block.

Environment overrides:

| Variable | Effect | Default |
|----------|--------|---------|
| `VIBE_TRADING_SEC_UA` | Replace the contact User-Agent with your own address | a Vibe-Trading contact string |
| `VIBE_TRADING_SEC_MIN_INTERVAL` | Raise the per-request spacing (never goes below the 0.12s floor) | `0.12` |

## Error handling

Network/HTTP failures propagate as `requests.RequestException` for the caller to classify (the `get_sec_filings` tool catches these and renders an error envelope). A bad CIK (no digits) raises `ValueError`. A malformed row inside the tickers payload is skipped rather than aborting the whole map.
