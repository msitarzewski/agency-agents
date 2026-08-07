# Loomloom Recruitment Screening SkillBot

This example adapts the evidence-based resume-screening guidance from
[`specialized/recruitment-specialist.md`](../../specialized/recruitment-specialist.md)
into a batch Loomloom SkillBot and a companion local PDF parsing Skill.

## Why this exists

Recruiters often receive resumes as PDFs, while a reusable Loomloom public
template needs normalized row-level text input. The local Skill extracts
traceable text from each PDF first. The public SkillBot then evaluates one
candidate against one job description per row, producing evidence-backed
screening output for human review.

The output is decision support only. It must not make final employment
decisions, infer protected characteristics, or replace recruiter review.

## Flow

```text
PDF resumes
  -> local pdf-resume-parser Skill
  -> normalized resume text + manifest
  -> one Loomloom workbook row per candidate
  -> evidence extraction
  -> qualification assessment
  -> consistency and compliance audit
  -> human-reviewed shortlist
```

## Contents

- `template-spec/recruitment-specialist-batch-resume-screening.spec.json`:
  private-template source used to create the public SkillBot.
- `skills/pdf-resume-parser/`: local Skill that converts PDF resumes into
  model-readable, traceable text.
- `generated-skill/loomloom-recruitment-specialist-batch-resume-screening/`:
  Loomloom-generated local Skill pinned to the validated private version, with
  a mandatory PDF-parser first step.
- `fixtures/resumes/`: synthetic PDF resumes used for testing.
- `fixtures/parsed/`: parser output generated from the synthetic resumes.
- `fixtures/job-description.txt`: synthetic role description used for testing.
- `results/`: Loomloom validation, run, and audit results. No credentials or
  real candidate data belong here.

## Validated private version

The tested private version fixes all three workflow steps to
`deepseek/deepseek-v4-flash`; users are not asked to select a model. A paid
validation run completed all three synthetic rows with no failed rows:

| Candidate | Score | Recommendation | Audit outcome |
| --- | ---: | --- | --- |
| `candidate-strong` | 88 | shortlist | corrected |
| `candidate-consider` | 55 | reject | needs human review |
| `candidate-reject` | 15 | reject | corrected |

See `results/run-summary.json`, `results/audit-summary.md`, and the downloaded
result workbook for the complete validation record. The measured run cost is a
test observation, not a performance or future-price guarantee.

The public SkillBot submission charges a creator fixed fee of CNY 0.01 per
successfully billed candidate row, with model/API cost charged separately. Its
identifiers and current review state are recorded in
`results/public-listing-submission.json`. At the time of this commit, the
listing is pending review and is not publicly executable.

## Public input contract

Each workbook row represents one candidate evaluated against one role.

| Field | Required | Meaning |
| --- | --- | --- |
| `candidate_id` | Yes | Stable, non-sensitive candidate identifier |
| `resume_text` | Yes | Text extracted from one PDF resume |
| `job_description` | Yes | Complete role responsibilities and requirements |
| `additional_screening_requirements` | No | Extra job-relevant constraints supplied by the recruiter |

The workbook retains `candidate_id` as the row-level trace key. The identifier
is not sent to the model; Loomloom associates each result with its source row.

The current DeepSeek private-template binding is recorded in
`results/private-template-v2.json`. That file contains identifiers only and
must never contain a credential.

## Local-first PDF preparation

The generated Loomloom local Skill must begin its execution workflow with this
instruction:

> First use the `pdf-resume-parser` Skill to convert every resume PDF into
> normalized, model-readable text before preparing the Loomloom input.

Run the parser directly when testing this repository:

```bash
python3 skills/pdf-resume-parser/scripts/parse_resume_pdfs.py \
  --input-dir fixtures/resumes \
  --output-dir fixtures/parsed
```

The parser writes one text file per resume, `manifest.json`, and
`resumes.jsonl`. A scanned PDF with no extractable text is reported as a hard
failure and must be OCR-processed before screening.

## Attribution and license

The screening methodology is adapted from The Agency's Recruitment Specialist
agent. The upstream repository is licensed under the MIT License:

- Source: https://github.com/msitarzewski/agency-agents
- Copyright (c) 2025 AgentLand Contributors

This example preserves the upstream copyright and permission notice. The
repository's top-level [`LICENSE`](../../LICENSE) applies.

## Privacy and employment safeguards

- Use synthetic or properly authorized candidate data only.
- Do not score age, gender, race, ethnicity, religion, disability, marital or
  parental status, photographs, addresses, or other protected/proxy traits.
- Do not treat missing information as negative evidence unless the job
  description explicitly identifies a lawful, job-related requirement.
- Require a human recruiter to review all recommendations and source evidence.
- Do not commit API tokens, raw production resumes, or unredacted personal data.
