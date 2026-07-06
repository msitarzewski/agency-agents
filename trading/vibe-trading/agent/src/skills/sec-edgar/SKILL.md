---
name: sec-edgar
description: U.S. SEC EDGAR fetch interface — resolve a ticker to its CIK, list recent filings (10-K / 10-Q / 8-K and friends) with primary-document URLs, and pull XBRL companyfacts financial series. Free, no API key; rate-limited by IP so every request is throttled and carries a contact User-Agent. United States only.
category: data-source
---
# SEC EDGAR

## Overview

The U.S. Securities and Exchange Commission (SEC) publishes free, no-auth JSON endpoints for every reporting company on its EDGAR system: a ticker-to-CIK directory, a recent-filings index, and the full set of XBRL ("companyfacts") financial concepts a company has reported. This skill documents how Vibe-Trading fetches that data through the bundled `sec_edgar_client` transport and the `get_sec_filings` agent tool.

This is the **fetch** skill — it covers how to get filing-index rows, document URLs, and us-gaap metric series out of EDGAR. The separate `edgar-sec-filings` skill is the **methodology** layer (how to read a 10-K, score insider activity, interpret 8-K items); for any actual data retrieval it delegates here.

Scope is the United States only. EDGAR has no coverage of A-shares, HK, or other non-U.S. markets — route those through `tushare` / `yfinance` / `akshare` instead.

> Link convention: every link below that points into `references/` is written with the **skill-name prefix** (`sec-edgar/references/...`). The `read_file` tool resolves paths with `skills/` as the root; dropping the prefix breaks the read. Keep the `<skill-name>/references/...` form when adding new docs.

## Quick Start

Preferred path — the `get_sec_filings` tool (read-only, throttled, returns strict JSON):

```json
{ "ticker": "AAPL", "form": "10-K", "limit": 5 }
```

```json
{ "ticker": "MSFT", "metric": "Revenues", "limit": 8 }
```

The tool resolves the ticker to a CIK, fetches the filing index (optionally filtered by `form`), and — when `metric` is set — also pulls the XBRL series for that us-gaap concept. See `sec-edgar/references/get_sec_filings_tool.md` for the full parameter and envelope contract.

Script path — call the `sec_edgar_client` transport directly when you need raw JSON the tool does not surface (e.g. company address, all units of a concept):

```python
from backtest.loaders.sec_edgar_client import cik_for, get_submissions, get_company_facts

cik = cik_for("AAPL")            # "0000320193", or None if not in the SEC table
submissions = get_submissions(cik)   # recent-filings index + company metadata
facts = get_company_facts(cik)       # all reported XBRL concepts
```

A runnable end-to-end example lives at `sec-edgar/scripts/sec_filings_example.py`.

## Parameter & Format Notes

- **Ticker**: U.S. equity symbol, case-insensitive (`AAPL`, `msft`). Resolved to a CIK via the SEC company-tickers table; an unlisted ticker returns an error envelope (tool) or `None` (`cik_for`).
- **CIK**: the SEC Central Index Key, normalized to a **zero-padded 10-digit** string (`320193` → `"0000320193"`). The submissions and companyfacts endpoints require the padded form; document URLs use the un-padded form.
- **Form**: SEC form type, case-insensitive (`10-K`, `10-Q`, `8-K`, `DEF 14A`, `4`). Omit to return all recent forms.
- **Metric**: an XBRL `us-gaap` concept name (`Revenues`, `NetIncomeLoss`, `Assets`, `StockholdersEquity`). Case-sensitive — these are exact taxonomy element names.
- **Dates**: SEC returns ISO `YYYY-MM-DD` strings (e.g. `2023-09-30`).
- **Return shape**: the tool returns a JSON-string envelope; the client returns decoded JSON (`dict`).

## Reference Docs

- [sec_edgar_client transport](sec-edgar/references/sec_edgar_client.md) — `cik_for`, `get_submissions`, `get_company_facts`, CIK padding, throttle bucket, contact User-Agent.
- [get_sec_filings tool](sec-edgar/references/get_sec_filings_tool.md) — parameters, success/error envelope, `filings[]` and `metric` field shapes.
- [Endpoints & rate limits](sec-edgar/references/endpoints_and_limits.md) — the three public endpoints, secid/CIK rules, fair-access policy, env overrides.
- [Common forms & XBRL concepts](sec-edgar/references/forms_and_concepts.md) — frequently used form types and us-gaap concept names.

## Scripts

- [End-to-end fetch example](sec-edgar/scripts/sec_filings_example.py) — ticker → CIK → recent 10-Ks → a metric series, using the bundled client.

## Notes

- **Free, no API key**: EDGAR is public. The only requirement is a descriptive `User-Agent` carrying a contact address; the client ships a compliant default and honors the `VIBE_TRADING_SEC_UA` override.
- **Rate-limited by IP**: the SEC throttles per source IP and temporarily blocks clients that burst without a contact UA. Every request routes through the shared `backtest.loaders._http` throttle under the `"sec"` host bucket (≈0.12s spacing floor, overridable via `VIBE_TRADING_SEC_MIN_INTERVAL`). Do not bypass the client with raw `requests` loops.
- **United States only**: a non-U.S. symbol will not resolve to a CIK.
- **Transport, not a backtest loader**: `sec_edgar_client` is a thin REST client, not a `DataLoaderProtocol`. There is no `source: "sec_edgar"` backtest mode — EDGAR feeds the `get_sec_filings` tool, not the bar-loading layer.
- **Reporting lag**: filings appear after the company submits; XBRL companyfacts trail the filing. Insider (Form 4) and 13F latency caveats are covered in the `edgar-sec-filings` methodology skill.
- **Research only**: this data supports research and does not constitute investment advice.
