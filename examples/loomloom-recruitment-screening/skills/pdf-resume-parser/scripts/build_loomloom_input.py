#!/usr/bin/env python3
"""Combine parsed resumes with a job description for Loomloom input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resumes-jsonl", type=Path, required=True)
    parser.add_argument("--job-description", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--additional-requirements", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    job_description = args.job_description.read_text(encoding="utf-8").strip()
    if not job_description:
        raise SystemExit("job description is empty")

    output_rows = []
    with args.resumes_jsonl.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            candidate_id = str(row.get("candidate_id", "")).strip()
            resume_text = str(row.get("resume_text", "")).strip()
            if not candidate_id or not resume_text:
                raise SystemExit(f"invalid parsed resume at line {line_number}")
            output_rows.append(
                {
                    "candidate_id": candidate_id,
                    "resume_text": resume_text,
                    "job_description": job_description,
                    "additional_screening_requirements": args.additional_requirements,
                }
            )

    if not output_rows:
        raise SystemExit("no parsed resumes found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    print(f"rows={len(output_rows)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
