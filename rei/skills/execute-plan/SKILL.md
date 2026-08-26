---
description: SKL - Execute an approved plan with minimal edits, repository-aware checks, and structured handoff sequencing.
---

# execute-plan

## Purpose

Orchestrate **post-approval** work: branch safety, minimal product changes, validation, tests, review, and optional PR prep. This is the umbrella skill for **implementation**; there is **no** separate “edit-only” skill—**how** to edit (boundaries, stacks) lives in workspace rules such as `.cursor/rules/architecture.mdc` and repo-specific `*.mdc` rules.

## Canonical cross-reference and precedence

- This is the canonical implementation execution skill.
- Routing and delegation defaults come from `.cursor/rules/orchestration.mdc`.
- Global branch/MCP/hook governance comes from `.cursor/rules/global.mdc`.
- Implementer role boundaries and final handoff expectations come from `.cursor/agents/implementer.md`.
- If instructions conflict, precedence is: direct user instruction in current chat -> protected-branch and safety constraints -> orchestration rule -> this skill -> role-specific details.

## When To Use

- After a plan exists under `plans/features/` or `plans/bugs/` and scope is approved (or the user waived formal planning but scope is clear).
- You are about to apply patches, run tests, or **Task → 🏠(REI) Implementer** (default per orchestration—not manual parent execution).

## Required Context

- Approved plan path (or explicit scope if no file).
- **Affected Repos** and canonical `feature/*` or `fix/*` branch name(s) from the plan.
- **`lessons.md`** at each touched repo root (see **Lessons learned** below).

## Lessons learned

Each git repo may keep **`lessons.md`** at its root (append-only institutional memory).

- **Before large edits:** skim `lessons.md` in each repo you will modify; avoid repeating documented mistakes.
- **Format for new entries** (Reviewer/Test-engineer): `## YYYY-MM-DD SEVERITY — summary — area — outcome` (per `.cursor/skills/review-diff/SKILL.md`).
- If missing when adding the first lesson: create with `# lessons.md — <repo folder name>` then append.
- Do not delete or rewrite past entries unless the user explicitly asks.

## Workflow

1. **branch-gate:** Run **`.cursor/skills/branch-gate/SKILL.md`** in **every** repo you will touch **before** the first `Write` / `StrReplace` / refactor or commit.
2. **Implement:** Apply the smallest change set that satisfies the plan; respect `.cursor/rules/architecture.mdc` and module boundaries. **Default:** **Task → 🏠(REI) Implementer** (`subagent_type="🏠(REI)  Implementer"`) per `.cursor/rules/orchestration.mdc`; parent in-chat edits only when the user explicitly opted out.
3. **Validate:** Run targeted tests, lint, or typecheck for touched repos (or document why skipped).
4. **Tests (behavior change):** Delegate to **🏠(REI) Test-engineer** (Task) and/or follow **`.cursor/skills/add-tests/SKILL.md`** so new or changed behavior is covered.
5. **Review:** Delegate to **🏠(REI) Reviewer** (Task) and/or follow **`.cursor/skills/review-diff/SKILL.md`** on the full diff (product + tests).
6. **PR readiness (required at ~95% done):** When coding is effectively complete and only integration/human review remains, include a required **Next Action** to create a PR to `DEV` via one-click compare link(s): `https://github.com/<owner>/<repo>/compare/DEV...<head>?expand=1`. For multi-repo work, provide one link per repo.
7. **PR preparation:** Use **`.cursor/skills/prepare-pr/SKILL.md`** to generate PR-ready title/body and publish-ready checklist.
8. **Optional (UI-heavy, on feature branch):** Suggest gstack **qa** / **design-review** per **`.cursor/skills/gstack-integration/SKILL.md`** before step 7—not instead of Test Engineer / Reviewer.

## Expected Deliverable

- Work completed on the correct `feature/*` or `fix/*` branches per repo; validation noted; Test/Review handoffs done per `.cursor/agents/implementer.md` unless waived there.
- A required completion note with one-click PR link(s) targeting `DEV` and explicit manual-approval instruction.

## Composition

**plan-feature** → **execute-plan** (this skill) → optional **prepare-pr**. Upstream discovery may use **🏠(REI) Researcher** before **plan-feature**.

## Safeguards

- No edits on protected branches (`main`, `master`, `DEV`, `develop`) without explicit user waiver; merges/pushes to them are user-only unless requested.
- No scope creep beyond the approved plan; ambiguous scope → **🏠(REI) Planner** or user, not silent expansion.
- Blocked work (secrets, env) → escalate to user; do not delegate Test/Review on incomplete or non-code work except per implementer waivers.
- Agents must not auto-approve PRs and must not auto-merge PRs unless the user explicitly requests that action in the current conversation.
