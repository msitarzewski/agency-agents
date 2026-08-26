---
description: SKL - Investigate codebase structure and dependencies to locate relevant implementation surfaces for the requested scope.
---

# investigate-codebase

## Purpose
Build a fast, evidence-based understanding of an unfamiliar feature area before making changes.

## When To Use

- Initial discovery for new tasks.
- Cross-repo issues where ownership is unclear.

## Required Context

- User request and known affected domain.
- Access to workspace search, key docs, and relevant modules.

## Workflow

0. If the next step is implementation (not just research), remind the user/implementer to run **branch-gate** so no repo stays on `DEV`/`main` while being edited.
1. Identify likely repos and entry points.
2. Gather authoritative docs/rules and active code paths.
3. Trace call/data flow across boundaries.
4. Capture conflicts, stale docs, and assumptions.
5. Provide recommended implementation starting points.

## Expected Deliverable

- Compact inventory: key files, ownership map, risks, and next steps.

## Safeguards

- Prefer current code evidence over stale documentation.
- Highlight uncertainty explicitly; do not guess hidden behavior.
