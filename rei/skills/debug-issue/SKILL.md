---
description: SKL - Debug a scoped issue from reproduction through minimal fix and validation in the owning repository.
---

# debug-issue

## Purpose

Systematically isolate and fix a defect with minimal regression risk.

## When To Use

- Reproducible bug reports.
- Failing tests, runtime errors, or unexpected behavior.

## When To Use Something Else

- **Ownership or architecture unclear** → **`.cursor/skills/investigate-codebase/SKILL.md`** first, then return to debugging or **`.cursor/skills/plan-feature/SKILL.md`** if the fix is large or cross-cutting.
- **User cannot reproduce and evidence is thin** → narrow hypotheses + ask for logs/steps; avoid shipping guesses.
- **Deep RCA requested** (user opt-in) → read **`.cursor/skills/gstack/investigate/SKILL.md`** after REI reproduce steps; still obey **branch-gate** before patches. See **`.cursor/skills/gstack-integration/SKILL.md`**.

## Required Context

- Reproduction steps, affected area, and expected vs actual behavior.
- Logs/errors and relevant code paths.

## Workflow

1. **Reproduce** and capture evidence.
   - If reproduction requires the local stack, use the **Real Estate CRM service manager MCP** (`user-real-estate-crm-service-manager`) to bring up services (`run_diagnostics` → `start_service` / `get_status`) rather than ad-hoc terminal commands.
   - For UI-only issues, use the **Playwright MCP** (`user-frontend-playwright`) to reproduce reliably and capture screenshots/network/console evidence.
2. **Narrow** root cause to a specific module/function/state transition (read-only tracing is OK on any branch).
3. **branch-gate:** Run **`.cursor/skills/branch-gate/SKILL.md`** in **every** repo you will **edit** before the first patch or commit—same rule as **`.cursor/skills/execute-plan/SKILL.md`**; debug flows often skip a formal plan file but still need a `fix/*` branch.
4. **Fix:** Implement the smallest change that addresses the root cause (no drive-by refactors).
5. **Tests:** Add regression coverage following **`.cursor/skills/add-tests/SKILL.md`** (branch-gate again if the test lives in a repo you have not branched yet).
6. **Validate:** Re-run relevant test/lint/typecheck commands; note what was run.

## Expected Deliverable

- Root-cause summary, fix details, tests added or justified if skipped, and validation evidence.

## Composition

Typical chain: **debug-issue** methodology inside **Task → 🏠(REI) Implementer** (or Planner → Implementer for large/ambiguous fixes). Parent must not patch by default (`.cursor/rules/orchestration.mdc`). After fix: **add-tests** → optional **review-diff** or **🏠(REI) Reviewer** for medium/high-impact changes.

## Safeguards

- Do not apply broad refactors while debugging unless required for correctness.
- If root cause remains uncertain, present ranked hypotheses and evidence gaps—do not guess.
- Prefer **lessons.md** at affected repo roots when present (see `.cursor/rules/lessons.mdc`).
