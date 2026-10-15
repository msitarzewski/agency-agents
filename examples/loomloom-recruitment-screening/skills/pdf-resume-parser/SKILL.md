---
name: pdf-resume-parser
description: Extract text from one or more PDF resumes into normalized, traceable text and JSONL before batch resume screening. Use when resume inputs are PDF files and a downstream AI workflow needs model-readable resume text.
---

# PDF Resume Parser

Convert PDF resumes into traceable text without evaluating candidates. This
Skill prepares input for the Loomloom Recruitment Specialist SkillBot.

## Required workflow

1. Confirm the source contains only synthetic data or candidate data the user
   is authorized to process.
2. Run `scripts/parse_resume_pdfs.py` on the supplied resume directory.
3. Review the parser summary and stop on any hard failure.
4. Use `resumes.jsonl` as the source of `candidate_id` and `resume_text` for the
   downstream Loomloom workbook or request.
5. Keep `manifest.json` with the downstream results so each conclusion remains
   traceable to its source PDF and SHA-256 digest.

## Command

```bash
python3 scripts/parse_resume_pdfs.py \
  --input-dir <resume-directory> \
  --output-dir <parsed-output-directory>
```

## Output

- `<candidate-id>.txt`: normalized resume text with page markers.
- `resumes.jsonl`: one object per successfully parsed PDF.
- `manifest.json`: source path, digest, parser, page count, character count,
  output path, status, and errors.

## Parsing rules

- Extract text only. Do not score, rank, summarize, or infer qualifications.
- Preserve source wording and page order so downstream evidence quotes remain
  auditable.
- Normalize Unicode and repeated whitespace only; do not rewrite content.
- Derive `candidate_id` from the filename and remove unsafe path characters.
- Treat empty output or fewer than 80 non-whitespace characters as a hard
  failure.
- Treat scanned/image-only PDFs as a hard failure requiring OCR before use.
- Never include API tokens or credentials in parser output.
- Do not commit real, unredacted candidate resumes or parsed personal data.

## Downstream handoff

The public SkillBot accepts text rather than `application/pdf`. For each parsed
record, combine `candidate_id` and `resume_text` with the relevant
`job_description` and optional `additional_screening_requirements`.
