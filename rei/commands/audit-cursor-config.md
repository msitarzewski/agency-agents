---
description: CMD - ⚡(REI) Audit Cursor architecture, duplication, layer placement, and context cost.
---

CMD - ⚡(REI) /audit-cursor-config

Broader than `/audit-token-efficiency`. Shared preamble: `.cursor/docs/audit-preamble.md`.

Use `cursor-config-architect` + `.cursor/skills/meta-skill/SKILL.md`. Do not edit files unless asked.

## Primary goals

Correct layer architecture, lower recurring tokens, smaller always-on context, less duplication, faster execution, maintainability.

## Architecture checks

Long workflows in rules; agents duplicating skills; commands duplicating workflows; MCP for prompting; subjective hooks; broad subagents; plugin file dumps.

## Token checks

Oversized always-on rules/agents; embedded examples/schemas; repeated cross-layer instructions; unnecessary always-read patterns; heavy MCP retrieval.

## Designer pack checks

Verify `.cursor/skills/design-*`, `ui-design`, `ux-strategy`, `interaction-design`, `prototyping-testing`, `designer-toolkit`; namespaced commands; resolvable skill paths; concise descriptions (verb + outcome + scope).

## Required output

1. Verdict
2. Architecture score (1–10) + token efficiency score (1–10)
3. Component inventory + audit table
4. Context cost analysis, high-cost components, misplaced logic, duplications, missing layers
5. Top 10 fixes (token savings × quality × ease)
6. Target architecture, files to add/change/remove, migration plan, validation checklist, estimated context reduction

Extended methodology: `.cursor/docs/meta-skill-reference.md`.
