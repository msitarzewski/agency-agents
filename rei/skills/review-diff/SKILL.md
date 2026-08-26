---
description: SKL - Review diffs for behavioral risk, missing safeguards, and test coverage adequacy before integration.
---

# review-diff

## Purpose
Run a structured, severity-based review of proposed code changes.

## When To Use

- Before creating or merging a PR.
- After implementation of medium/high-impact changes.

## Required Context

- Current branch and diff versus base branch.
- Intended behavior from plan/spec.

## Workflow

1. Confirm the diff’s **source** branch is a plan-named `feature/*` or `fix/*` (not accidentally `DEV`/`main` as the work head). Inspect diff and map changed files to affected repos.
2. Validate correctness, regression risk, security, data integrity, and repo boundaries.
3. If the change impacts runtime behavior (async effects, data-fetching, auth flows, UI state), prefer quick runtime verification:
   - Use the **Real Estate CRM service manager MCP** (`user-real-estate-crm-service-manager`) to check prerequisites and bring up services:
     - `run_diagnostics`
     - `get_status`
     - `start_service` (`frontend`, `backend`, or `all`) when needed
   - Use the **Playwright MCP** (`user-frontend-playwright`) for targeted UI checks (login, open drawer, verify expected UI state), not exhaustive automation.
   - For **full live-app QA or visual fix loops** on a `feature/*` or `fix/*` branch (after Implementer), suggest gstack **`.cursor/skills/gstack/qa/SKILL.md`** or **`.cursor/skills/gstack/design-review/SKILL.md`** with **browse** (requires `gstack/setup`). See **`.cursor/skills/gstack-integration/SKILL.md`**.
4. Classify findings: `HIGH`, `MEDIUM`, `LOW`.
5. Provide concrete fixes for each finding.
6. Call out missing tests and coverage gaps, including wrong test placement (tests must live in the relevant repo and test-type folder).
7. For **MEDIUM** and **HIGH** issues, **append** a new `##` heading per finding to each affected repo’s **`lessons.md`** per workspace **`lessons.mdc`** (so future planner/implementer runs benefit).

## Expected Deliverable

- Findings-first report with severity, impacted files, and clear remediation actions.

## Composition

Typically runs on the full diff after **`.cursor/skills/add-tests/SKILL.md`** (or **🏠(REI) Test-engineer**) when tests were part of the change. **🏠(REI) Reviewer** (Task) should follow this skill. Next step for the user is often **`.cursor/skills/prepare-pr/SKILL.md`** once findings are addressed.

## Canonical cross-reference and precedence

- This file is canonical for review workflow, severity grading, and finding structure.
- Agent files should remain role-oriented and reference this skill for procedure details.
- If review-procedure instructions conflict between an agent and this skill, follow this skill.

## Safeguards

- Prioritize risk over style.
- If no findings, state that explicitly and note residual risk/gaps.
- Do not require runtime verification for purely mechanical changes (typos, copy, non-functional refactors) unless the diff is risky.
