---
description: CMD - ⚡(REI) Route new_feature, adjust_feature, and small_improvement through design/planning/implementation/test/review.
---

CMD - ⚡(REI) /deliver

Single entrypoint for non-bug product work. Preserves REI orchestration defaults (`.cursor/rules/orchestration.mdc`).

## Intents

`new_feature` | `adjust_feature` | `small_improvement` — ask once if missing or ambiguous.

## Required inputs

Target outcome, owning repo(s)/surface, constraints. Ask concise questions if missing.

## Routing

1. UX/product behavior changing → `/design-product` (Security Design Brief: `.cursor/docs/security-gates.md`).
2. After **🏠(REI) product-designer** → auto-route per orchestration (Implementer if implementation-ready, else Planner → `plans/features/`).
3. Planner used → stop for plan approval unless waived (`.cursor/docs/step-transition-contract.md`).
4. Implementer → Test-engineer → Reviewer (`.cursor/agents/implementer.md`, `.cursor/skills/execute-plan/SKILL.md`).

## Not for

Bug-first root-cause work (`/fix-bug`). Release/deploy (`/release`).
