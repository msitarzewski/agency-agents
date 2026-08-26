---
description: SKL - Produce an implementation-ready feature plan with explicit scope, steps, and repository-specific validation criteria.
---

# plan-feature

## Purpose

Create an implementation-ready plan for feature or bug work in a multi-repo workspace.

## When To Use

- The request is non-trivial, ambiguous, or touches multiple repos.
- You need a change manifest before coding.
- Workspace orchestration (`.cursor/rules/orchestration.mdc`) calls for **🏠(REI) Planner** / this skill instead of ad hoc planning in the parent chat.

## Required Context

- Request details and success criteria.
- Prefer **Task** with `subagent_type="🏠(REI) Planner"` (see `.cursor/rules/orchestration.mdc`, `.cursor/agents/planner.md`) when the role is “write a formal plan,” unless the user asked for a quick informal outline only.
- Relevant repo docs and existing plans under `plans/features/` or `plans/bugs/`.
- **`lessons.md`** at the root of each impacted repo (if present)—read before finalizing risks and scope.

## Workflow

1. Classify the request as `feature` or `fix`.
2. Identify impacted repos and architecture boundaries (nested repo vs workspace root—see step 5).
3. Read relevant prior plans, `lessons.md` where present, and conventions.
4. **Git branches (mandatory in plan):** One canonical `feature/<slug>` or `fix/<slug>` (kebab-case, aligned with the plan title). State base branch per repo if non-default (e.g. `DEV`). Implementation must not start until those branches exist and the implementer is checked out on them—unless the user explicitly waives branch creation in chat.
5. **Affected Repos:** List every git repo that will hold edits. Nested product repos (`real-estate-crm-*`, etc.) are separate from the workspace root. Include the **workspace root** only when the change manifest includes paths outside nested repos (e.g. `plans/`, root-only files). Branch **in the repo that owns the files**—not only at the root when all code is inside a nested repo.
6. Choose output path at workspace root:
   - Feature: `plans/features/YYYY-MM-DD-<slug>.md`
   - Bug fix: `plans/bugs/YYYY-MM-DD-<slug>.md`
7. Draft the plan: summary, **Affected Repos**, **Branch** line(s) and per-repo branching rules, file-level change manifest, risks, out-of-scope, open questions.
8. Save the plan to the selected path and reference that exact path in the final response.
9. Stop on unresolved ambiguity; do not fabricate decisions.

## Expected Deliverable

- A saved markdown file under `plans/features/` or `plans/bugs/`, with content sufficient for **branch-gate** (`.cursor/skills/branch-gate/SKILL.md`) and **🏠(REI) Implementer** handoff.
- When acting as the Planner subagent, prefer **preview-mode** / structured plan output per `.cursor/agents/planner.md` unless the user asked for markdown-style formatting.

## Composition

Typical chain: **plan-feature** (this skill) → **execute-plan** (`.cursor/skills/execute-plan/SKILL.md`; wraps **branch-gate**, implementation, validation, tests, review) → prefer **🏠(REI) Implementer** (Task) which delegates Test Engineer + Reviewer per `.cursor/agents/implementer.md`. If discovery is still incomplete: **🏠(REI) Researcher** first, then return here.

Optional upstream (greenfield / strategy): gstack pre-plan skills via **`.cursor/skills/gstack-integration/SKILL.md`** (`office-hours`, `plan-ceo-review`, `plan-eng-review`)—do not skip saving this plan artifact.

## Canonical cross-reference and precedence

- This file is canonical for feature/fix planning workflow.
- Agent files should define boundaries and routing only; avoid duplicating this playbook.
- If planning instructions conflict between an agent and this skill, follow this skill.

## Safeguards

- No implementation during planning.
- No hidden scope expansion.
- Do not instruct or imply that coding may begin on `main`/`master`/`DEV`/`develop` without an explicit user exception; the plan must name dedicated `feature/*` or `fix/*` branches and correct per-repo checkout behavior.
