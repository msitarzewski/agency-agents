---
description: SKL - Add high-signal tests that verify changed behavior and risk paths in the target repository scope.
---

# add-tests

## Purpose
Add focused regression and behavior tests for changed code.

## When To Use

- Any bug fix or behavior change.
- New logic paths, validation, async flows, or integration boundaries.

## Required Context

- Changed files and intended behavior.
- Existing test structure in impacted repos.

## Workflow

0. If you will modify tracked source or tests in a repo, run **branch-gate** (`.cursor/skills/branch-gate/SKILL.md`) in that repo first.
1. Identify behavior deltas and risk-heavy paths.
2. Select proper framework by repo (`Jest/Supertest`, RTL, `pytest`).
   - For frontend bugs that depend on real browser behavior (routing, drawer/tab state, auth redirects, async rendering), include targeted **Playwright MCP** checks using `user-frontend-playwright`.
   - If local services are required for runtime checks, use `user-real-estate-crm-service-manager` (`run_diagnostics`, `start_service`, `get_status`) instead of ad-hoc startup scripts.
3. Choose test destination per impacted repo and test type:
   - Backend: `tests/unit`, `tests/integration`, `tests/e2e` (or repo-equivalent).
   - Frontend: repo-native unit/integration/e2e locations.
   - Scraper: `tests/` with unit/integration/system grouping when present.
   - Extension: extension-repo test folders by test intent/type.
4. Add tests for happy path, edge cases, and failure paths.
5. Run targeted test commands and iterate until green.
6. Document remaining coverage gaps if any.

## Expected Deliverable

- Test files saved in each relevant repo under the correct test-type directory, plus a short test plan proving changed behavior.

## Composition

Typically follows product changes from **`.cursor/skills/execute-plan/SKILL.md`** or **`.cursor/skills/debug-issue/SKILL.md`**. **🏠(REI) Test-engineer** (Task) should follow this skill. Downstream: **`.cursor/skills/review-diff/SKILL.md`** on the combined product + test diff, then optional **`.cursor/skills/prepare-pr/SKILL.md`**.

## Canonical cross-reference and precedence

- This file is canonical for test strategy, placement, and validation flow.
- Agent files should keep boundary/handoff guidance and reference this skill for testing procedure details.
- If testing-procedure instructions conflict between an agent and this skill, follow this skill.

## Safeguards

- Avoid brittle tests coupled to implementation details.
- Prefer deterministic assertions over snapshots-only coverage.
- Use Playwright selectively for high-risk UI paths; avoid turning every change into long browser suites.
