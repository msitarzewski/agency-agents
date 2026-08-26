---
description: SKL - Enforce safe work-branch setup before edits or commits across all repositories being modified.
---

# branch-gate

## Purpose
Prevent implementation work from landing on protected integration branches (`DEV`, `main`, etc.) by requiring an explicit `feature/*` or `fix/*` checkout **before** any code changes.

## When To Use

- **Always** before the first implementation edit (search_replace, write, refactor) or `git commit` in any workspace repo for a feature or bug fix.
- After reading a plan that names `feature/<slug>` or `fix/<slug>`.

## Workflow

1. Identify which git repos you will modify. **Branch in the repo that owns the files**, not by habit at the workspace root:
   - Each nested project (`real-estate-crm-backend`, `real-estate-crm-frontend`, `real-estate-crm-chrome-extension`, `real-estate-crm-scraper`, `HomeHarvestLocal`, …) is its **own** git repository.
   - For every path you will edit, that file’s repository is the **innermost** clone containing it (e.g. edits under `real-estate-crm-backend/src/...` → run all `git` commands from `real-estate-crm-backend/`, not from the monorepo-style workspace root).
   - Use the **workspace root** repo’s branch **only** when you change files tracked there and **not** solely under a nested repo (e.g. workspace-level `plans/`, `reviews/`, root `AGENTS.md`, or other root-only paths). If **all** edits live inside one nested repo, do **not** create the work branch only at the workspace root.
2. In **each** repo you will touch, run:
   - `git branch --show-current`
   - If the branch is `main`, `master`, `DEV`, or `develop` (or another protected name listed in `.cursor/rules/global.mdc`): **stop editing** until you run  
     `git checkout -b fix/<slug>` or `git checkout -b feature/<slug>`  
     (use the **exact** slug from the plan; base branch = plan’s stated base, usually `DEV` or `main`).
   - If the branch is already `feature/<slug>` or `fix/<slug>` and matches the plan, proceed.
3. Multi-repo work: repeat step 2 in **every** affected repo with the **same** branch name.
4. Only after step 2 passes for all target repos, apply patches/commits.

## Protected branches are never valid work branches

Do not implement on `DEV`, `main`, `master`, or `develop`.  
If currently on a protected branch, stop and create/switch to the planned `feature/*` or `fix/*` branch before any edits.

## Expected Deliverable

- Confirmation in your reasoning (not necessarily user-visible spam) that each edited repo is on the correct work branch **before** file edits.

## Safeguards

- Never assume "we will branch later" after code is already changed on a protected branch.
- Never open a PR from protected branch as the feature head unless the user explicitly requested that workflow.

## Composition

Used by **`.cursor/skills/execute-plan/SKILL.md`**, **`.cursor/skills/debug-issue/SKILL.md`**, **`.cursor/skills/add-tests/SKILL.md`**, **`.cursor/skills/plan-feature/SKILL.md`** (downstream implementers), and **`.cursor/skills/prepare-pr/SKILL.md`** (PR branch sanity). Always run **before** the first edit or commit on a work item.

## Canonical cross-reference and precedence

- This file is canonical for branch safety checks before edits/commits.
- Other skills and agents should reference this gate instead of re-stating branch-check procedures in full.
- If branch-gate instructions conflict with another doc, follow this skill unless the user explicitly waives.
