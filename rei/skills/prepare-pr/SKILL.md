---
description: SKL - Prepare a merge-ready pull request with clear summary, validation evidence, and policy-compliant metadata.
---

# prepare-pr

## Purpose
Prepare a high-quality pull request with clear scope, validation, and risk communication.

## When To Use

- Code is complete and you are opening a PR (or need a PR-ready title/body).
- After **`.cursor/skills/review-diff/SKILL.md`** / **🏠(REI) Reviewer** when findings are resolved or only LOW, and you are ready to describe the change for humans.
- Not a substitute for review—summarize work that is already validated.

## Required Context

- Branch diff, commits, and test results.
- Any linked plan/spec and known tradeoffs.

## Workflow

1. Confirm the PR source branch matches the plan: `feature/*` or `fix/*` per repo (not `main`/`master`/`DEV` as the feature head unless explicitly agreed). Use **branch-gate** expectations from `.cursor/skills/branch-gate/SKILL.md`. Review full branch delta from base.
2. Default PR base branch to `DEV` unless the user explicitly specifies a different base.
3. Provide a one-click PR compare link: `https://github.com/<owner>/<repo>/compare/DEV...<head>?expand=1` (or matching explicit base override).
4. Summarize why the change exists and what behavior changed.
5. Include test plan and executed validation commands.
6. List risks, migrations, rollout notes, and follow-ups (if any).
7. Ensure PR body is concise, scannable, and actionable for reviewers.
8. Include explicit manual governance note: PR approval and merge are human-only unless user explicitly asks agents to perform those actions.

## Expected Deliverable

- PR-ready title/body and checklist with risk/test context.
- One-click compare link (or one per affected repo) targeting `DEV` by default.
- Explicit note that approval/merge are manual human steps by default.

## Composition

Usually **last** in the chain: **execute-plan** → (optional **add-tests** / Test Engineer) → **review-diff** / Reviewer → **prepare-pr** (this skill). Relies on **branch-gate** expectations for branch naming.

## Safeguards

- No vague "misc fixes" summaries.
- Do not hide known limitations or skipped tests.
- Do **not** invoke gstack **`ship`** in the same flow unless the user explicitly chose gstack release automation (see **`.cursor/rules/gstack-integration.mdc`**).
- Do not merge or push to protected branches (`main`, `master`, `DEV`, `develop`); the user integrates those manually.
- Do not auto-approve PRs and do not auto-merge PRs unless the user explicitly requests those actions.
