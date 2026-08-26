# Audit command preamble (shared)

Used by `/audit-cursor-config` and `/audit-token-efficiency`.

## Invocation

- Agent: `cursor-config-architect`
- Skill: `.cursor/skills/meta-skill/SKILL.md`
- Do not edit files unless explicitly asked.

## Method (every component)

1. Purpose
2. Load frequency: Always-On | Frequently Loaded | Occasionally Loaded | Reference Only
3. Token risk: Low | Medium | High
4. Duplication / misplacement (architecture audit) or context bloat (token audit)
5. Recommendation: Keep | Shorten | Split | Merge | Scope | Convert to Reference | Move to Another Layer | Delete

## Scope

`.cursor/rules`, `.cursor/agents`, `.cursor/skills`, `.cursor/commands`, `.cursor/mcp`, `.cursor/hooks`, plugins, reference docs.

Extended schemas and builder playbooks: `.cursor/docs/meta-skill-reference.md`.
