# EDGAR endpoints, identifiers & rate limits

All public, free, no-auth JSON. Source of truth for the URLs and rules the `sec_edgar_client` is built on.

## Endpoints

| Purpose | URL | Keyed by |
|---------|-----|----------|
| Ticker → CIK directory | `https://www.sec.gov/files/company_tickers.json` | — (full table) |
| Filing index (submissions) | `https://data.sec.gov/submissions/CIK{cik}.json` | padded 10-digit CIK |
| XBRL company facts | `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | padded 10-digit CIK |

Primary-document URLs are assembled, not fetched as JSON:

```
https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/{accession_no_dashes}/{primary_document}
```

`accession_no_dashes` is the accession number with its hyphens removed (`0000320193-23-000106` → `000032019323000106`).

## Identifiers

- **CIK (Central Index Key)**: the SEC's per-filer numeric id. The submissions and companyfacts endpoints require it **zero-padded to 10 digits** (`320193` → `0000320193`). Document URLs use the **un-padded** form (`320193`).
- **Ticker**: case-insensitive; resolved to a CIK through `company_tickers.json`. A `company_tickers.json` row looks like `{"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}`.
- **Accession number**: per-filing id, dashed form `0000320193-23-000106`.

## Rate limits & fair access

The SEC rate-limits **by source IP** and asks every client to send a descriptive `User-Agent` that carries a contact address. The documented ceiling is ~10 requests/second; bursting without a contact UA earns a temporary block.

The client therefore:

- routes every request through the shared `backtest.loaders._http` throttle under the `"sec"` host bucket, enforcing a ~0.12s per-request spacing floor;
- sends a compliant contact `User-Agent` by default.

### Environment overrides

| Variable | Effect | Default |
|----------|--------|---------|
| `VIBE_TRADING_SEC_UA` | Replace the contact User-Agent (use your own address) | a Vibe-Trading contact string |
| `VIBE_TRADING_SEC_MIN_INTERVAL` | Raise per-request spacing; never drops below the 0.12s floor | `0.12` |

## Coverage & lag

- **United States only.** EDGAR has no non-U.S. coverage; non-U.S. symbols will not resolve to a CIK.
- Filings appear after submission; XBRL companyfacts trail the filing itself. Reporting-lag nuances for Form 4 (insider) and 13F live in the `edgar-sec-filings` methodology skill.
