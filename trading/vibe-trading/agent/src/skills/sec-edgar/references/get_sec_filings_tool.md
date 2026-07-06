# get_sec_filings — agent tool

Tool name: `get_sec_filings` (class `SecFilingsTool`, module `src.tools.sec_filings_tool`)

Read-only tool that wraps the `sec_edgar_client` transport behind the project's `BaseTool` contract. One call answers two questions: a list of recent filings, and (optionally) the reported XBRL us-gaap series for one financial concept. Auto-discovered via the tool registry; the agent never touches `sec.gov` un-throttled.

Markets: United States only.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `ticker` | string | yes | — | U.S. equity ticker, case-insensitive (`AAPL`, `msft`). Resolved to a CIK via the SEC company-tickers table. |
| `form` | string | no | all forms | SEC form type filter, case-insensitive (`10-K`, `10-Q`, `8-K`). Omit to return every recent form. |
| `metric` | string | no | — | XBRL `us-gaap` concept name (`Revenues`, `NetIncomeLoss`, `Assets`). When set, the response also carries that concept's reported series. Case-sensitive. |
| `limit` | integer | no | `20` | Max number of most-recent filings and metric points to return. Clamped to `1..40`. |

## Success envelope

```json
{
  "ok": true,
  "market": "US",
  "source": "sec_edgar",
  "data": {
    "ticker": "AAPL",
    "cik": "0000320193",
    "filings": [
      {
        "form": "10-K",
        "accession_number": "0000320193-23-000106",
        "filing_date": "2023-11-03",
        "report_date": "2023-09-30",
        "primary_document": "aapl-20230930.htm",
        "description": "10-K",
        "document_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"
      }
    ],
    "metric": {
      "concept": "Revenues",
      "unit": "USD",
      "label": "Revenues",
      "points": [
        {
          "end": "2023-09-30",
          "val": 383285000000.0,
          "fiscal_year": 2023,
          "fiscal_period": "FY",
          "form": "10-K",
          "accession": "0000320193-23-000106",
          "frame": "CY2023"
        }
      ]
    }
  }
}
```

- `source` is the literal `"sec_edgar"` — it tags the data origin in the envelope; it is **not** a backtest `source` value (EDGAR is not a bar loader).
- `filings` is newest-first (as the SEC returns it), filtered to `form` when given, capped at 40.
- `metric` is present only when the `metric` parameter is supplied. The tool picks the unit bucket with the most rows; `points` is the most-recent `limit` entries. `unit` / `points` are empty when the concept is absent or carries no data.
- `document_url` is `null` when the SEC row lacks an accession number or primary-document filename.

## Error envelope

```json
{ "ok": false, "error": "ticker 'XYZ' not found in the SEC company table (US only)" }
```

Returned for: missing/blank `ticker`; a ticker absent from the SEC table; or any underlying fetch failure (ticker lookup, submissions, or companyfacts). A single failing fetch yields an error envelope rather than raising.

## Examples

```json
{ "ticker": "AAPL", "form": "10-K", "limit": 5 }
```

```json
{ "ticker": "NVDA", "metric": "NetIncomeLoss", "limit": 12 }
```

```json
{ "ticker": "TSLA", "form": "8-K", "limit": 10 }
```

## Notes

- `get_sec_filings` is an agent + CLI tool. For deeper interpretation (reading MD&A, scoring insider/8-K signals), pair it with the `edgar-sec-filings` methodology skill, which delegates here for fetching.
- The tool surfaces a compact subset; for raw fields (company address, every unit of a concept) call the `sec_edgar_client` functions directly.
