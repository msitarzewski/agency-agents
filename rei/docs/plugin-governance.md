# Plugin Governance

## Component Lifecycle

Use one of:

- active
- experimental
- superseded
- deprecated

## Change Rules

Before adding a component:

1. Check if an existing component should be updated instead.
2. Classify the correct layer.
3. Confirm no duplicated logic.
4. Confirm the component has a clear trigger.
5. Add validation steps.

## Review Checklist

- Is the purpose clear?
- Is the layer correct?
- Is this component reusable?
- Is always-on context minimized?
- Are edit permissions clear?
- Are failure modes handled?
- Is the plugin still coherent?

## Deprecation Policy

Deprecate rather than silently delete when another team/user may depend on the component.

Mark deprecated components with:

```txt
status: deprecated
superseded_by: <component-name>
reason: <short reason>
```

## Imported Packs

- designer-skills-import: active
  - source: `claude code designer-skills-main` (local snapshot import)
  - scope: namespaced commands and plugin-scoped skills under `.cursor`
  - notes: phase-1 additive migration, no destructive removals
- product-designer-agent: active
  - path: `.cursor/agents/product-designer.md`
  - use when: product design requests need explicit mode routing across imported design skills
- gstack-rei-integration: active
  - install: `scripts/install-gstack-cursor-skills.ps1` → `.cursor/skills/gstack/` (copies + truncated descriptions; not committed; re-run after gstack pull)
  - router: `.cursor/skills/gstack-integration/SKILL.md`
  - rule: `.cursor/rules/gstack-integration.mdc`
  - commands: `gstack-pre-plan`, `gstack-qa`, `gstack-design-review`, `gstack-plan-design-review`, `gstack-ship`, `gstack-deploy`, `gstack-security-audit`
  - docs: `.cursor/docs/gstack-rei-integration.md`
  - notes: REI orchestration and `prepare-pr` remain canonical; gstack `ship` is opt-in only
- workflow-routing-assistant: active
  - agent: `.cursor/agents/workflow-guide.md`
  - command: `.cursor/commands/workflow-guide.md`
  - docs: `.cursor/docs/command-map.md`
  - notes: routing-only helper for command selection across `/deliver`, `/fix-bug`, `/design-product`, and `/release`

Review checklist extension:
- Are namespaced command/skill names collision-safe against existing workspace components?

