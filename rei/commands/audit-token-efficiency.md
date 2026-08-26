---
description: CMD - ⚡(REI) Audit Cursor configuration for token usage, context bloat, and load-frequency risk.
---

CMD - ⚡(REI) /audit-token-efficiency

Narrower than `/audit-cursor-config`. Shared preamble: `.cursor/docs/audit-preamble.md`.

Use `cursor-config-architect` + `.cursor/skills/meta-skill/SKILL.md`. Do not edit files unless asked.

## Focus

- Recurring token usage, always-on and frequently loaded context
- Duplicated instructions, oversized rules/agents/skills
- Unnecessary skill loading, excessive MCP retrieval
- Reference material loaded as active instructions

## Layer checks

**Rules:** global rules that should be scoped, workflow in rules, duplicated skills, broad alwaysApply.

**Agents:** teach vs orchestrate, embedded examples/schemas, duplicated skill logic.

**Skills:** multi-capability skills, reference material that should split, overly broad invocation.

**Commands:** duplicate full skills, unclear routing.

**MCP:** oversized payloads, missing limits, capability without workflow value.

**Hooks:** unnecessary runs, slow/subjective hooks.

## Required output

1. Token Efficiency Score (1–10)
2. Largest recurring context consumers
3. Always-on + frequently loaded audits
4. Duplicate logic inventory
5. Component table: Component | Type | Load Frequency | Token Risk | Estimated Waste | Recommendation
6. Top 10 quick wins (savings × ease × risk)
7. File-level changes, reference moves, shorten/scope/merge/delete lists
8. Estimated context reduction %
9. Post-refactor validation steps

Prioritize high-ROI changes; preserve working behavior.
