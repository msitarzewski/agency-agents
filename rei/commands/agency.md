# Agency — list or activate an Agency agent

Read `.cursor/catalog/roster.json` (or `catalog/by-division/<division>.md`) and help the user pick a subagent.

## Behavior

1. If the user names a slug or role, activate that Cursor subagent (Task with `subagent_type` = slug, e.g. `backend-architect`).
2. If the user names a division, list matching slugs from the catalog.
3. If unclear, ask one clarifying question, then recommend 1–3 agents.
4. Do not dump full agent bodies into the chat; delegate to the subagent instead.

Installed agents live in `.cursor/agents/<slug>.md`.

## With REI orchestration

When REI is installed (`.cursor/rules/orchestration.mdc`):

- `/agency` picks **domain specialists** (engineering, security, …).
- **Delivery** still goes through 🏠(REI) Planner → Implementer → Test-engineer → Reviewer.
- **Design / UX / UI:** prefer `/design-product` (designer-skills). Do **not** recommend Agency design-division agents for routine design — only when product-designer states the pack is a poor fit (see `agency-integration` § Design).
- Routing table: `.cursor/skills/agency-integration/SKILL.md`.
- Do not use Agency specialists to bypass an approved plan or branch-gate.
