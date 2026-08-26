---
description: CMD - ⚡(REI) Canonical product design gateway that routes to product-designer and enforces required input questioning plus Security Design Brief coverage.
---

CMD - Route product design work to product-designer agent (designer-skills default).

CMD - ⚡(REI) /design-product

Purpose: **Default / sole** product-design command for this workspace. Prefer this over Agency design-division agents.

## Policy

1. **Always start** with **🏠(REI) product-designer** + `.cursor/skills/design-pack/SKILL.md` (designer-skills).
2. Use Agency design slugs (`ui-designer`, `ux-researcher`, `brand-guardian`, …) **only** when the pack cannot cover the need — see `.cursor/skills/agency-integration/SKILL.md` § Design.
3. Do not open `/agency` for routine UX/UI; use `/agency` design division only after stating a fit failure.

## Required inputs

- target user/persona and primary problem
- target surface/repo and device context
- constraints (timeline, brand/accessibility level, business goal)

If required inputs are missing, ask concise clarifying questions before producing artifacts.

## Security Design Brief (mandatory)

Design outputs must include:

- data classification
- trust boundaries
- abuse cases
- auth/authz expectations
- privacy constraints
- security acceptance criteria

## Route

- Agent: **🏠(REI) product-designer** (Task `subagent_type="🏠(REI) product-designer"`)
- Router: `.cursor/agents/product-designer.md`
- Pack: `.cursor/skills/design-pack/SKILL.md`
- Optional gstack phases: `.cursor/skills/gstack-integration/SKILL.md`

## Post-design automatic routing policy

After `🏠(REI) product-designer` returns artifacts, routing is automatic and does not require user route selection:

- Route directly to **🏠(REI) Implementer** only when the design output is implementation-ready:
  - scope is locked
  - architecture boundaries are clear
  - API/data contracts and edge cases are explicit
  - validation criteria are explicit
  - implementation sequence is obvious
- Otherwise route to **🏠(REI) Planner** first.
- If uncertain or mixed, default to **🏠(REI) Planner**.

## Step-finish messaging (required)

When design work completes, report transition state per `.cursor/docs/step-transition-contract.md`:

- `Step complete: ...`
- `Current state: ...`
- `Next required action: ...`

If the next step is approval-gated (for example, Planner output requiring approval), the message must request the exact approval/waiver reply.

## Use

Any UX/UI request: research, flows, screens, interaction specs, handoff, pre-build design review, or live design QA.

## Not for

Production backend/frontend implementation or bug root-cause remediation; use `/deliver` or `/fix-bug`.
