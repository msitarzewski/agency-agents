# Cursor AI Operating Model

**User guides:** [Global/docs/cursor-rei-guide.md](../../Global/docs/cursor-rei-guide.md) (how to use agents, commands, skills, rules) · [Global/docs/gstack-rei-integration.md](../../Global/docs/gstack-rei-integration.md) (optional gstack)

## Core Principle

Each part of the Cursor configuration stack has one job.

```txt
Rules    = persistent defaults
Agents   = orchestration workers
Subagents = specialized workers
Skills   = reusable methodology
Commands = manual workflow launchers
MCP      = external capability layer
Hooks    = deterministic automation
Plugins  = packaging/distribution layer
```

## Decision Matrix

| Need | Put it in |
|---|---|
| Always-on repo standard | Rule |
| Specialized AI role | Subagent (REI delivery **or** Agency domain slug) |
| Main execution behavior | Agent |
| Reusable workflow/playbook | Skill (`agency-integration`, `gstack-integration`, …) |
| Manual shortcut | Command (`/agency`, `/plan-feature`, …) |
| External tool/data access | MCP |
| Event-triggered automation | Hook |
| Shareable bundled capability | Plugin |

## Recommended Workflow Pattern

1. User invokes command.
2. Command stays thin and routes to canonical agent/subagent + skill.
3. Agent/subagent uses relevant skill.
4. Root rules in `.cursor/rules/*.mdc` shape default behavior.
5. MCP provides external data/tools if justified.
6. Hooks run deterministic validation.
7. Plugin packages the capability.

## Canonical Path Notes

- Always-on governance is centralized at root `.cursor/rules/*.mdc`.
- Legacy nested rule files under repo-local `.cursor/rules/` are retired.
- Command files under `.cursor/commands/` are wrappers only and should not duplicate skill playbooks.
