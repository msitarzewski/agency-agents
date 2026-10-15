#!/usr/bin/env python3
"""Extract traceable text from PDF resumes for downstream AI screening."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


MIN_TEXT_CHARS = 80


@dataclass
class ParseRecord:
    candidate_id: str
    source_file: str
    source_sha256: str
    parser: str
    page_count: int
    character_count: int
    output_file: str
    status: str
    errors: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_id_from_path(path: Path) -> str:
    normalized = unicodedata.normalize("NFKC", path.stem).strip().lower()
    candidate_id = re.sub(r"[^a-z0-9._-]+", "-", normalized).strip("-._")
    return candidate_id or hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:12]


def normalize_page_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\x00", "")
    lines = []
    for raw_line in text.splitlines():
        line = re.sub(r"[\t ]+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def extract_with_pdfplumber(path: Path) -> list[str]:
    import pdfplumber  # type: ignore

    with pdfplumber.open(path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def extract_with_pypdf(path: Path) -> list[str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def extract_with_pdftotext(path: Path) -> list[str]:
    process = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return process.stdout.split("\f")


def available_extractors() -> list[tuple[str, Callable[[Path], list[str]]]]:
    extractors: list[tuple[str, Callable[[Path], list[str]]]] = []
    try:
        import pdfplumber  # noqa: F401

        extractors.append(("pdfplumber", extract_with_pdfplumber))
    except ImportError:
        pass
    try:
        import pypdf  # noqa: F401

        extractors.append(("pypdf", extract_with_pypdf))
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        extractors.append(("pdftotext", extract_with_pdftotext))
    return extractors


def extract_pdf(path: Path, extractors: list[tuple[str, Callable[[Path], list[str]]]]) -> tuple[str, str, int]:
    failures: list[str] = []
    for parser_name, extractor in extractors:
        try:
            pages = extractor(path)
            rendered_pages = []
            for index, page in enumerate(pages, start=1):
                normalized = normalize_page_text(page)
                rendered_pages.append(f"[Page {index}]\n{normalized}")
            text = "\n\n".join(rendered_pages).strip()
            if len(re.sub(r"\s+", "", text)) >= MIN_TEXT_CHARS:
                return parser_name, text, len(pages)
            failures.append(f"{parser_name}: extracted text is too short")
        except Exception as exc:  # pragma: no cover - backend-specific failures
            failures.append(f"{parser_name}: {exc}")
    raise RuntimeError("; ".join(failures) or "no PDF text extractor is available")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.is_dir():
        print(f"error: input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    pdf_files = sorted(
        path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"
    )
    if not pdf_files:
        print(f"error: no PDF files found under {input_dir}", file=sys.stderr)
        return 2

    extractors = available_extractors()
    if not extractors:
        print("error: install pdfplumber or pypdf, or install the pdftotext command", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[ParseRecord] = []
    jsonl_rows: list[dict[str, str]] = []
    used_ids: set[str] = set()

    for pdf_path in pdf_files:
        candidate_id = candidate_id_from_path(pdf_path)
        if candidate_id in used_ids:
            candidate_id = f"{candidate_id}-{sha256_file(pdf_path)[:8]}"
        used_ids.add(candidate_id)
        text_path = output_dir / f"{candidate_id}.txt"
        try:
            parser_name, resume_text, page_count = extract_pdf(pdf_path, extractors)
            text_path.write_text(resume_text + "\n", encoding="utf-8")
            record = ParseRecord(
                candidate_id=candidate_id,
                source_file=str(pdf_path.relative_to(input_dir)),
                source_sha256=sha256_file(pdf_path),
                parser=parser_name,
                page_count=page_count,
                character_count=len(resume_text),
                output_file=text_path.name,
                status="parsed",
                errors=[],
            )
            jsonl_rows.append({"candidate_id": candidate_id, "resume_text": resume_text})
        except Exception as exc:
            record = ParseRecord(
                candidate_id=candidate_id,
                source_file=str(pdf_path.relative_to(input_dir)),
                source_sha256=sha256_file(pdf_path),
                parser="",
                page_count=0,
                character_count=0,
                output_file="",
                status="failed",
                errors=[str(exc)],
            )
        records.append(record)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps({"records": [asdict(record) for record in records]}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    jsonl_path = output_dir / "resumes.jsonl"
    jsonl_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in jsonl_rows),
        encoding="utf-8",
    )

    parsed_count = sum(record.status == "parsed" for record in records)
    failed_count = len(records) - parsed_count
    print(f"parsed={parsed_count} failed={failed_count} output={output_dir}")
    for record in records:
        if record.status == "failed":
            print(f"failed: {record.source_file}: {'; '.join(record.errors)}", file=sys.stderr)
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
