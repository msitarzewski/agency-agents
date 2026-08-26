---
description: CMD - ⚡(REI) Build or improve a Cursor plugin architecture with clear component boundaries and minimal recurring context cost.
---

CMD - ⚡(REI) /build-cursor-plugin

Use the `cursor-config-architect` agent and the `meta-skill`.

Build or improve a Cursor plugin architecture.

If editing is allowed, create the minimal coherent plugin scaffold.

## Primary Goals

Design a plugin that is:

1. Coherent
2. Installable
3. Maintainable
4. Minimal in recurring context cost
5. Clear in component boundaries
6. Free of duplicated methodology
7. Practical for real Cursor workflows

## Required Design Rules

For every generated or modified component:

1. Define its purpose.
2. Define its Cursor layer:
   - rule
   - agent
   - subagent
   - skill
   - command
   - MCP
   - hook
   - plugin doc
   - reference doc
3. Classify load frequency:
   - Always-On
   - Frequently Loaded
   - Occasionally Loaded
   - Reference Only
4. Classify token risk:
   - Low
   - Medium
   - High
5. Justify any always-on component.
6. Move long examples, schemas, and reference material to reference-only docs.
7. Avoid duplicating Meta Skill methodology inside agents or commands.
8. Prefer router agents over knowledge-heavy agents.
9. Prefer commands as thin workflow entry points.
10. Prefer skills for reusable methodology.
11. Prefer scoped rules over global rules.
12. Prefer MCP only when external capability is truly needed.
13. Prefer hooks only for deterministic automation.

## Component Size Guidelines

Use these as guidelines, not hard limits:

| Component | Recommended Size |
|---|---:|
| Global Rule | 100-300 words |
| Scoped Rule | 200-600 words |
| Frequently Used Agent | 300-800 words |
| Specialized Agent | 500-1500 words |
| Skill | 600-2000 words |
| Command | 50-300 words |
| Reference Document | No practical limit |

Larger recurring-context components require explicit justification.

## Description Requirements

For every discoverable component:

- include a concise human-readable description
- use one sentence where practical
- start with an action verb
- state outcome plus scope
- avoid vague wording such as “helper”, “stuff”, “misc”, or “general”

Required for:

- commands
- agents
- subagents
- skills

Recommended for:

- rules
- plugins
- reference docs

## Required Output

Return:

1. Plugin purpose
2. Target user
3. Recommended architecture
4. Component map
5. Component load-frequency table:

| Component | Type | Load Frequency | Token Risk | Scope | Notes |
|---|---|---|---|---|---|

6. File tree
7. Key file contents
8. Installation assumptions
9. Commands exposed
10. MCP requirements
11. Hook requirements
12. Context cost analysis
13. Token-risk reduction actions
14. Validation checklist
15. Maintenance notes