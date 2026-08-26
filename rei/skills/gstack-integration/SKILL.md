---
description: SKL - Route REI workflow phases to optional gstack skills without overriding branch policy, orchestration, or canonical REI skills.
---

# gstack-integration

## Purpose

Tell REI agents and commands **which gstack skill to use, when, and what not to duplicate**. gstack fills gaps REI does not cover (pre-plan product review, live browser QA, release automation, deploy verify, security audit).

## Prerequisites

1. Run **`scripts/install-gstack-cursor-skills.ps1`** from the workspace root (copies skills into `.cursor/skills/gstack/` and truncates frontmatter descriptions for discovery; re-run after `gstack` git pull).
2. For browser QA: run **`gstack/setup`** (Git Bash or WSL) once to build the browse binary.
3. Human guides: **`Global/docs/gstack-rei-integration.md`**, **`Global/docs/cursor-rei-guide.md`**.

Skill paths (after install): `.cursor/skills/gstack/<skill-name>/SKILL.md`

## REI canonical vs gstack optional

| Phase | REI (always for product code) | gstack (optional) |
|-------|------------------------------|-------------------|
| Idea / product framing | — | `office-hours`, `plan-ceo-review` |
| Architecture / plan critique (pre-`plans/`) | — | `plan-eng-review`, `autoplan` |
| Design rubric (pre-build) | designer pack + `product-designer` | `plan-design-review` (0–10 rubric) |
| Executable multi-repo plan | `plan-feature` + 🏠 Planner | — |
| Discovery | `investigate-codebase` + Researcher | — |
| Debug (narrow) | `debug-issue` | `investigate` (deep RCA; user opt-in) |
| Implement | `execute-plan` + Implementer | — |
| Unit/integration tests | `add-tests` + Test-engineer | — |
| Diff review | `review-diff` + Reviewer | `review` (deep pre-land; user opt-in) |
| Live app QA | Playwright MCP (spot) | `qa`, `qa-only`, `design-review` + `browse` |
| PR packaging | `prepare-pr` | — |
| Release automation | — | `ship` (user opt-in only) |
| Post-merge deploy | — | `land-and-deploy`, `canary` |
| Security audit | — | `cso` |
| Design artifacts | designer pack skills | `design-consultation`, `devex-review` |
| Docs after ship | — | `document-release` |
| Retro / health | — | `retro`, `health` |

## Agent mapping

| REI agent | gstack skills (read when relevant) |
|-----------|-----------------------------------|
| **🏠 Planner** | Suggest `office-hours` / `plan-ceo-review` / `plan-eng-review` **before** `plan-feature` when scope is greenfield or ambiguous. Do not replace saved `plans/` artifacts. |
| **🏠 Researcher** | — |
| **🏠 Implementer** | After code complete on `feature/*`/`fix/*`, suggest `qa` or `design-review` if UI-heavy; never `ship` by default. |
| **🏠 Test-engineer** | — |
| **🏠 Reviewer** | May suggest gstack `review` for high-risk diffs; keep `review-diff` as primary. |
| **product-designer** | `plan-design-review`, `design-review`, `design-consultation`, `devex-review` + full designer pack (see agent file). |
| **cursor-config-architect** | — |

## Agency Agents

Domain specialists (Agency subagents) are **not** gstack. See `.cursor/skills/agency-integration/SKILL.md`. Do not use gstack skills to substitute for Agency `backend-architect` / `frontend-developer` / etc.

## Workflow (combined REI + gstack)

1. (Optional) gstack pre-plan skills → user alignment.
2. 🏠 **Planner** + **plan-feature** → `plans/features/` or `plans/bugs/` → **user approves**.
3. 🏠 **Implementer** + **execute-plan** + **branch-gate**.
4. 🏠 **Test-engineer** → 🏠 **Reviewer**.
5. (Optional) gstack **qa** / **design-review** on the same feature branch.
6. **prepare-pr** → human PR to `DEV`.
7. (Optional, after merge) gstack **land-and-deploy** + **canary**.

## Safeguards

- gstack `ship` must not target protected branches as the work branch; REI PR base remains **`DEV`** unless the user states otherwise.
- Do not invoke gstack skills that **push** or **merge** without explicit user request.
- If `.cursor/skills/gstack/` is missing, tell the user to run `scripts/install-gstack-cursor-skills.ps1`.

## Composition

- Upstream: `.cursor/rules/orchestration.mdc`, `.cursor/rules/global.mdc`
- Downstream: individual `.cursor/skills/gstack/*/SKILL.md`
