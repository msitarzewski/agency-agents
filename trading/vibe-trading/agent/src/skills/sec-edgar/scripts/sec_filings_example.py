#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end SEC EDGAR fetch example.

Resolves a ticker to its CIK, lists recent 10-K filings with their primary
document URLs, and prints a single XBRL us-gaap metric series — all through the
bundled, IP-throttled ``sec_edgar_client`` transport (no API key required).

Run from the ``agent/`` directory so that ``backtest`` resolves on the path::

    python -m src.skills.sec-edgar.scripts.sec_filings_example
    # or
    python src/skills/sec-edgar/scripts/sec_filings_example.py
"""

from typing import Any, Dict, List, Optional

from backtest.loaders.sec_edgar_client import (
    cik_for,
    get_company_facts,
    get_submissions,
)

_DOC_BASE = "https://www.sec.gov/Archives/edgar/data"


def resolve_cik(ticker: str) -> Optional[str]:
    """Resolve a U.S. ticker to its zero-padded 10-digit CIK.

    Args:
        ticker: A U.S. equity ticker, case-insensitive (e.g. ``"AAPL"``).

    Returns:
        The padded CIK string, or ``None`` when the ticker is not in the SEC
        company table.
    """
    try:
        cik = cik_for(ticker)
    except Exception as exc:  # noqa: BLE001 - example: report and continue
        print(f"CIK lookup failed for {ticker}: {exc}")
        return None
    if cik is None:
        print(f"Ticker not found in the SEC table (US only): {ticker}")
    return cik


def recent_filings(cik: str, form: str, limit: int) -> List[Dict[str, Any]]:
    """List recent filings of one form type for a CIK, newest first.

    Args:
        cik: A padded or un-padded CIK.
        form: SEC form type to keep (e.g. ``"10-K"``), case-insensitive.
        limit: Maximum number of filings to return.

    Returns:
        A list of normalized filing dicts; empty on fetch failure or no match.
    """
    try:
        submissions = get_submissions(cik)
    except Exception as exc:  # noqa: BLE001 - example: report and continue
        print(f"submissions fetch failed for CIK {cik}: {exc}")
        return []

    recent = (submissions.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    accessions = recent.get("accessionNumber") or []
    filing_dates = recent.get("filingDate") or []
    primary_docs = recent.get("primaryDocument") or []

    want = form.strip().upper()
    cik_unpadded = str(cik).lstrip("0") or "0"
    out: List[Dict[str, Any]] = []
    for idx, raw_form in enumerate(forms):
        if str(raw_form).strip().upper() != want:
            continue
        accession = accessions[idx] if idx < len(accessions) else None
        doc = primary_docs[idx] if idx < len(primary_docs) else None
        url = None
        if accession and doc:
            url = f"{_DOC_BASE}/{cik_unpadded}/{str(accession).replace('-', '')}/{doc}"
        out.append(
            {
                "form": str(raw_form).strip(),
                "accession_number": accession,
                "filing_date": filing_dates[idx] if idx < len(filing_dates) else None,
                "document_url": url,
            }
        )
        if len(out) >= limit:
            break
    return out


def metric_series(cik: str, concept: str, limit: int) -> List[Dict[str, Any]]:
    """Pull the most-recent points of one us-gaap concept for a CIK.

    Args:
        cik: A padded or un-padded CIK.
        concept: An XBRL ``us-gaap`` concept name (e.g. ``"Revenues"``).
        limit: Maximum number of most-recent points to return.

    Returns:
        A list of ``{end, val, fiscal_year, fiscal_period}`` points; empty when
        the concept is absent or the fetch fails.
    """
    try:
        facts = get_company_facts(cik)
    except Exception as exc:  # noqa: BLE001 - example: report and continue
        print(f"companyfacts fetch failed for CIK {cik}: {exc}")
        return []

    concept_block = ((facts.get("facts") or {}).get("us-gaap") or {}).get(concept)
    if not isinstance(concept_block, dict):
        print(f"concept not reported: {concept}")
        return []

    units = concept_block.get("units") or {}
    # Pick the unit bucket with the most rows (usually USD for monetary concepts).
    rows: List[Any] = []
    for candidate in units.values():
        if isinstance(candidate, list) and len(candidate) >= len(rows):
            rows = candidate

    points = [
        {
            "end": r.get("end"),
            "val": r.get("val"),
            "fiscal_year": r.get("fy"),
            "fiscal_period": r.get("fp"),
        }
        for r in rows
        if isinstance(r, dict)
    ]
    return points[-limit:] if limit > 0 else points


def main() -> None:
    """Run the example for a single ticker."""
    ticker = "AAPL"
    print(f"===== SEC EDGAR fetch example: {ticker} =====")

    cik = resolve_cik(ticker)
    if cik is None:
        return
    print(f"CIK: {cik}")

    print("\nRecent 10-K filings:")
    for filing in recent_filings(cik, form="10-K", limit=3):
        print(f"  {filing['filing_date']}  {filing['accession_number']}")
        print(f"    {filing['document_url']}")

    print("\nRevenues (most recent points):")
    for point in metric_series(cik, concept="Revenues", limit=5):
        print(
            f"  {point['end']}  {point['val']}  "
            f"FY{point['fiscal_year']} {point['fiscal_period']}"
        )


if __name__ == "__main__":
    main()
