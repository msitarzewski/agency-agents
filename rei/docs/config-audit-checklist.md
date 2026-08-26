# Cursor Configuration Audit Checklist

## Inventory

- [ ] Rules
- [ ] Agents
- [ ] Subagents
- [ ] Skills
- [ ] Commands
- [ ] MCP servers
- [ ] Hooks
- [ ] Plugins
- [ ] Docs

## Placement

- [ ] Rules are concise and persistent
- [ ] Skills contain reusable methodology
- [ ] Commands are thin workflow launchers
- [ ] Subagents are specialized
- [ ] MCP exposes external capabilities only
- [ ] Hooks are deterministic and safe
- [ ] Plugin bundles a coherent capability

## Duplication

- [ ] Agents do not duplicate skill logic
- [ ] Commands do not duplicate skill logic
- [ ] Rules do not contain long workflows
- [ ] Skills do not overlap heavily
- [ ] Subagents do not duplicate each other

## Invocation Flow

For each common workflow, map:

```txt
Command -> Agent/Subagent -> Skill(s) -> Rule(s) -> MCP -> Hook(s) -> Output
```

## Validation

- [ ] There is a test/manual validation path
- [ ] Failure behavior is defined
- [ ] Users know how to invoke the workflow
- [ ] Deprecated components are marked
