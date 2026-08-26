---
description: CMD - ⚡(REI) Canonical bug workflow — Planner, approval, Implementer, test, review.
---

CMD - ⚡(REI) /fix-bug

Orchestration entrypoint only; procedures live in referenced skills/agents.

## Required inputs

Observed vs expected behavior, affected repo/surface, reproduction context. Ask if missing.

## Default chain (unless opted out)

1. **Task → 🏠(REI) Planner** → save under `plans/bugs/`.
2. **STOP** for separate plan approval (`.cursor/docs/step-transition-contract.md`). "please fix" / "continue" alone do not waive.
3. **Task → 🏠(REI)  Implementer** after approval or explicit waiver.
4. Test-engineer → Reviewer per `.cursor/agents/implementer.md`.

## Security gates

`.cursor/docs/security-gates.md`

## Skills

`.cursor/skills/plan-feature/SKILL.md`, `branch-gate`, `execute-plan`, `add-tests`, `review-diff`

## Opt-out

Main-chat execution only on explicit opt-out (`.cursor/rules/orchestration.mdc` § Explicit opt-out). Ask once if ambiguous.

## Notes

No commit/merge by default; PR flow and human approval for protected branches.
