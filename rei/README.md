# REI overlay (Cursor delivery pipeline)

Source of truth for **REI** + **designer-skills**, shipped with this Agency Agents fork.

## Included

| Layer | Contents |
|-------|----------|
| REI agents | Planner, Implementer, Test-engineer, Reviewer, Researcher, product-designer, cursor-config-architect, workflow-guide |
| REI rules | Thin workspace rules + `agency-integration.mdc` + `orchestration.mdc` (no Agency persona `.mdc` dump) |
| REI workflow skills | `plan-feature`, `execute-plan`, `branch-gate`, `add-tests`, `review-diff`, `agency-integration`, … |
| **Designer-skills** | Full local snapshot of [Owl-Listener/designer-skills](https://github.com/Owl-Listener/designer-skills): **63** `SKILL.md` files across 8 plugins + `design-pack` router |
| Commands | `/design-product`, `/plan-feature`, `/implement-plan`, `/agency`, … |

### Designer plugins (verified vs upstream snapshot)

| Plugin | Skills in `rei/skills/` |
|--------|-------------------------|
| design-research | 10 |
| design-systems | 8 |
| ux-strategy | 8 |
| ui-design | 9 |
| interaction-design | 7 |
| prototyping-testing | 8 |
| design-ops | 7 |
| designer-toolkit | 6 |
| **Total** | **63** |

Entry points: **🏠(REI) product-designer** + `/design-product` + `skills/design-pack/SKILL.md`.

## Install

```bash
./scripts/convert.sh --tool cursor          # Agency pack only
./scripts/install.sh --tool cursor --with-rei --division engineering,testing,product
```

- **Not converted** by `convert.sh` — Cursor-native; install merges into `.cursor/`.
- **gstack** is optional and **not** part of this overlay’s required install path (see `gstack-integration` if you wire it separately).

## Agency wiring

`skills/agency-integration/SKILL.md` + `rules/agency-integration.mdc` — REI delivery stays canonical; Agency specialists are optional Task depth.
