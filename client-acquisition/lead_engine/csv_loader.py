"""Simple CSV lead intake for the private local acquisition pipeline."""

import csv
from pathlib import Path
from typing import List

from orchestrator.models import Lead


REQUIRED = {"company_name"}


def load_leads(path: Path) -> List[Lead]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

        leads: List[Lead] = []
        for row_number, row in enumerate(reader, start=2):
            company = (row.get("company_name") or "").strip()
            if not company:
                raise ValueError(f"Row {row_number}: company_name is required")
            metadata = {
                key: value.strip()
                for key, value in row.items()
                if key not in {"company_name", "contact_name", "contact_email", "website", "source"}
                and value
            }
            leads.append(
                Lead(
                    company_name=company,
                    contact_name=(row.get("contact_name") or "").strip() or None,
                    contact_email=(row.get("contact_email") or "").strip() or None,
                    website=(row.get("website") or "").strip() or None,
                    source=(row.get("source") or "").strip() or None,
                    metadata=metadata,
                )
            )
        return leads
