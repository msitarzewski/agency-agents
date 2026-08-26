# REI overlay for Agency Agents Cursor install

## Source of truth

Canonical REI files live in the repo root:

```text
rei/
  agents/     # 🏠(REI) Planner, Implementer, …
  rules/      # thin workspace rules + agency-integration.mdc
  skills/     # plan-feature, execute-plan, agency-integration, …
  commands/
  docs/
  hooks/
  mcp/
  README.md
```

These are **not** produced by `convert.sh`. They are Cursor-native and versioned as raw data.

Legacy note: `integrations/cursor/rei-overlay/` pointed here historically; use `rei/` only.

## Install

```bash
./scripts/convert.sh --tool cursor   # Agency pack only
./scripts/install.sh --tool cursor --with-rei --division engineering,testing,product
```

| Flag | Behavior |
|------|----------|
| *(default)* | If `rei/agents` exists, merge REI after Agency pack |
| `--with-rei` | Require merge; error if `rei/` missing |
| `--no-rei` | Agency pack only |

`install_cursor` copies Agency first, then merges REI (REI wins on shared rule/command/skill names; Agency slug agents remain).

## Precedence

REI orchestration > Agency specialists > optional gstack. See `rei/skills/agency-integration/SKILL.md`.
