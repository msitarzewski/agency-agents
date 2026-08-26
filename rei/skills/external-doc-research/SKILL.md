---
description: SKL - Research external source-of-truth documentation and extract actionable facts for the current implementation scope.
---

# external-doc-research

## Purpose
Collect, normalize, and synchronize external documentation into concise, reusable internal notes for agent execution.

## When To Use

- A task depends on third-party platform behavior or API expectations.
- Existing internal notes are stale, incomplete, or missing.
- You need deterministic assumptions before implementation or review.

## Required Context

- Task scope and affected repo/module.
- Target provider name and source-of-truth URL.
- Existing files under `docs/external/` and `docs/external/registry.md`.

## Workflow

1. Identify provider and verify source-of-truth URL(s).
2. Read only the relevant external pages for the task scope.
3. Extract concise facts: constraints, required fields, limits, and workflow rules.
4. Update or create provider notes under `docs/external/<provider>/notes.md`.
5. Update `docs/external/registry.md` with owner, last-verified date, source-of-truth, and status.
6. Add explicit `Assumptions` and `Unknowns` sections when evidence is incomplete.

## Expected Deliverable

- Updated provider notes with actionable facts and traceable source links.
- Registry row updated with current verification metadata.
- Clear assumptions/unknowns that unblock safe implementation.

## Safeguards

- Do not paste large external doc dumps; summarize only task-relevant facts.
- Keep notes deterministic: separate confirmed facts from assumptions.
- If sources conflict, flag the conflict and defer to runtime/code evidence.
