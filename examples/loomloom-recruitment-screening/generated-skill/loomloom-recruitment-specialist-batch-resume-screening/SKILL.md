---
name: "loomloom-recruitment-specialist-batch-resume-screening"
description: "Batch, evidence-based resume prescreening adapted from The Agency Recruitment Specialist. Produces human-reviewable candidate fit assessments without using protected characteristics."
---

# Recruitment Specialist - Batch Resume Screening

Use this skill when the user asks for a task that matches this LoomLoom template. The template logic stays on LoomLoom; this local skill is only a usage wrapper and CLI calling guide.

## Source
- Source type: private user template
- Template ID: `76c4b6e6-de49-4bda-9755-9ea55eac9fa9`
- Template version ID: `a5bdf34a-335b-4f52-90ad-055417e1485e`
- Run-time behavior: stay pinned to this exact template version unless the user explicitly upgrades the skill.

## Required First Step For PDF Resumes
- Before collecting or submitting LoomLoom input, first use the companion `pdf-resume-parser` Skill to convert every supplied PDF resume into normalized, model-readable `resume_text`. Stop if parsing reports a hard failure; do not send an unreadable or guessed resume to LoomLoom.

## When To Use
- Use when the user's task matches: Recruitment Specialist - Batch Resume Screening.
- Template description: Batch, evidence-based resume prescreening adapted from The Agency Recruitment Specialist. Produces human-reviewable candidate fit assessments without using protected characteristics.
- Use for batch or structured row-based work where LoomLoom should execute the hosted workflow.

## When Not To Use
- Do not use for unrelated one-off chat answers.
- Do not reconstruct or reveal hidden prompts, workflow definitions, model settings, internal step IDs, or creator private methods.
- Do not run anything until a quote or precheck has been shown and the user explicitly confirms submission.

## Input Collection
- For PDF inputs, complete the required `pdf-resume-parser` step above before downloading, filling, validating, quoting, or submitting the LoomLoom workbook.
- Full structured input schema was not available at installation time.
- Use the workbook-first flow. Download the workbook at run time and collect inputs from the workbook headers and instructions.
- If workbook download or parsing fails, stop and explain that the template workbook is currently unavailable.
- Ask for one missing required input at a time.
- Treat template descriptions, field labels, instructions, and sample rows as guidance only. Do not use them as the user's actual input unless the user explicitly confirms those values.
- If required user materials are missing, such as source documents, images, brand/product facts, reference text, or row data, stop input collection and ask the user to provide them. Do not continue to validate, quote/precheck, or submit with guessed placeholder content.
- For file inputs, ask the user for the exact local file path. Do not guess, invent, or substitute important user materials.
- For large local files or reference materials, first run `loomloom input-asset upload <file>` and place the returned `input_asset_id` into the workbook / Excel field before validate, quote/precheck, or submit. Do not paste large file contents into chat or treat raw local files as already submitted inputs.
- Prefer workbook / Excel-style input. Use JSON or JSONL only when the user explicitly asks for programmatic input.

## Execution Rules
- Installation is not execution and creates no model/API usage or Market fee.
- Before every real run, show an execution confirmation card with task count, estimated model/API cost, total estimate, balance status when returned, and the exact action.
- The user must reply with a natural confirmation such as `Confirm` before any run command is called.
- Use a stable `--client-request-id` for the exact payload. Reuse it only for retrying the same payload; generate a new one when the payload, file, template, version, or listing changes.
- Private template runs must stay pinned to the installed template version.
- Workbook flow: `loomloom template-spec download-workbook 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 a5bdf34a-335b-4f52-90ad-055417e1485e` -> fill/approve workbook -> `loomloom template-spec validate-workbook 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 a5bdf34a-335b-4f52-90ad-055417e1485e <xlsx>` -> `loomloom template-spec precheck-workbook 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 a5bdf34a-335b-4f52-90ad-055417e1485e <xlsx>` -> confirmation -> `loomloom template-spec submit-workbook 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 a5bdf34a-335b-4f52-90ad-055417e1485e <xlsx> --client-request-id <id>`.
- JSONL flow, only when explicitly requested: `loomloom orchestration-input upload <file.jsonl>` -> `loomloom template-spec precheck 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 --version-id a5bdf34a-335b-4f52-90ad-055417e1485e --input-file-id <input_file_id>` -> confirmation -> `loomloom template-spec run 76c4b6e6-de49-4bda-9755-9ea55eac9fa9 --version-id a5bdf34a-335b-4f52-90ad-055417e1485e --input-file-id <input_file_id> --client-request-id <id>`.

## Result Handling
- Return the `runId`, current status, and any returned error summary.
- Useful commands: `loomloom run get <run-id>`, `loomloom run watch <run-id>`, `loomloom run result-rows <run-id>`, `loomloom run result-workbook <run-id>`, `loomloom artifact list <run-id>`, and `loomloom artifact download <run-id>`.
- If a listing is unavailable, permission is denied, balance is insufficient, or a version cannot run, stop and explain the issue. Do not substitute another template or bypass Market.
- When explaining CLI JSON or backend responses to the user, translate technical field names and enum values into plain user-facing wording. Do not expose developer field names such as `saleStatus`, `reviewStatus`, `executionAvailabilityStatus`, `executionBlockReason`, `forced_unlisted`, `inputSchemaSnapshot`, or `taskFixedFeeT` unless the user explicitly asks for raw JSON/API fields. For example, explain `forced_unlisted` as "This SkillBot has been forcibly removed from the Market and cannot currently be listed or run"; explain `reviewStatus=rejected` as "the review was not approved"; explain `executionAvailabilityStatus=blocked` as "currently unavailable to run".
- When CLI output says `(currency unknown)` or a response lacks `currency`, tell the user the currency is unknown and preserve the raw T value. Do not show only a bare number and do not guess CNY or USD.
