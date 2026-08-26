---
description: SKL - Route REI workflow phases to Agency Agents specialists without overriding orchestration, branch policy, or canonical REI skills.
---

# agency-integration

## Purpose

Tell REI agents and commands **which Agency Agents subagents/skills to use, when, and what not to duplicate**. Agency fills **domain expertise** gaps (backend, frontend, API, security specialists). REI remains the **delivery pipeline**.

## Prerequisites

1. Agency Cursor pack installed: `.cursor/agents/<slug>.md` exists (from `agency-agents` `install.sh --tool cursor`).
2. Prefer selective install: `--division engineering,security,testing,product` (avoid full 269 unless needed).
3. Catalog: `.cursor/catalog/roster.json` and `.cursor/catalog/by-division/`.
4. Discovery command: `/agency` (`.cursor/commands/agency.md`).

## Precedence (never invert)

1. User instruction for this turn  
2. Branch / security safeguards (`global.mdc`, `branch-gate`, `security-gates.md`)  
3. **REI orchestration** (Planner → approve → Implementer → Test → Reviewer)  
4. This skill (Agency specialists)  
5. Optional gstack (`gstack-integration`)  

Agency specialists **consult / deepen**; they do **not** replace Planner, Implementer, Test-engineer, Reviewer, or **product-designer** for normal delivery/design.

## Design (important)

| Priority | Path |
|----------|------|
| **Default (regular)** | `/design-product` → 🏠(REI) **product-designer** → `design-pack` + designer-skills leaves |
| **Exception only** | Agency design division via Task / `/agency` when the pack is a **poor fit** (see table below) |

**Do not** default UX/UI work to Agency `ui-designer` / `ux-researcher` / etc. Those are overflow specialists.

### When Agency design *is* appropriate

| Need (pack gap) | Agency slug |
|-----------------|-------------|
| Brand identity / positioning | `brand-guardian` |
| AI image / photo prompts | `image-prompt-engineer` |
| Inclusive / non-stereotypical visuals | `inclusive-visuals-specialist` |
| Live-page CRO / persona scroll walkthrough | `persona-walkthrough-specialist` |
| Extra visual polish beyond ui-design leaves | `ui-designer` |
| Anti-generic UI finish gate | `ui-finish-gate-reviewer` |
| Large-scale IA / UX architecture | `ux-architect` |
| Research methodology beyond design-research leaves | `ux-researcher` |
| Brand narrative / multimedia story | `visual-storyteller` |
| Intentional whimsy / delight injection | `whimsy-injector` |

Before spawning any of the above, state one sentence: why designer-skills/design-pack cannot cover it.

## REI canonical vs Agency optional

| Phase | REI (always for product code) | Agency (optional specialist) |
|-------|------------------------------|------------------------------|
| **Product design / UX / UI** | **`/design-product` + product-designer + design-pack** | Design division **only** on pack fit failure (table above) |
| Idea / framing | — | — (optional gstack `office-hours`) |
| Executable plan | `plan-feature` + 🏠 Planner | Consult `software-architect` / `backend-architect` / `product-manager` for plan inputs |
| Discovery | `investigate-codebase` + Researcher | `codebase-onboarding-engineer` for unfamiliar trees |
| Implement | `execute-plan` + Implementer | Spawn specialist Task mid-implementation when depth needed (see map) |
| Unit/integration tests | `add-tests` + Test-engineer | `test-automation-engineer`, `api-tester` |
| Diff review | `review-diff` + Reviewer | `code-reviewer` (secondary opinion); security → security division |
| Live QA | Playwright MCP / gstack `qa` | — |
| Cursor config | `cursor-config-architect` | — |

## How to invoke Agency

- **Task** with `subagent_type` = agent frontmatter `name` (slug), e.g. `backend-architect`, `frontend-developer`.
- Or `/agency` then name a slug/division.
- If a matching **skill** exists at `.cursor/skills/<slug>/SKILL.md`, the subagent may load it; do not paste skill bodies into REI agents.
- **Do not** install or re-enable Agency personas as `.mdc` rules.

## Domain → slug map (code-heavy)

| Need | Primary Agency slug | Also consider |
|------|---------------------|---------------|
| Backend / services (Python, Node, APIs) | `backend-architect` | `api-platform-engineer`, `software-architect` |
| React / web **implementation** | `frontend-developer` | (UI *design* → product-designer first, not Agency design) |
| Product design / UX / UI **design** | — (use REI product-designer) | Design division only on pack fit failure |
| Cross-cutting system design | `software-architect` | `backend-architect` |
| Auth / SSO / tenancy | `identity-access-engineer` | `privacy-engineer`, `security-architect` |
| Payments / billing | `payments-billing-engineer` | `backend-architect` |
| Schema / queries | `database-optimizer` | `database-reliability-engineer` |
| Data pipelines | `data-engineer` | `ai-engineer` |
| Fast MVP slice | `rapid-prototyper` | `minimal-change-engineer` |
| Security review depth | `application-security-engineer` | `senior-secops-engineer`, `penetration-tester` |
| Diff quality opinion | `code-reviewer` | (REI Reviewer stays primary) |
| Tests / E2E | `test-automation-engineer` | `api-tester`, `performance-benchmarker` |
| Real-estate CRM domain UX | `real-estate-buyer-seller` | sales/support division as needed |
| AI features in product | `ai-engineer` | `rag-pipeline-engineer`, `prompt-engineer` |

For anything else: `/agency` + division name, or search `.cursor/catalog/roster.json`.

## Agent mapping (REI → Agency)

| REI agent | When to call Agency |
|-----------|---------------------|
| **🏠 Planner** | Before or while drafting `plans/`: Task → specialist for architecture/API/data/auth uncertainty; fold advice into the plan. Do not skip saved `plans/` artifacts. |
| **🏠 Researcher** | Prefer Agency `codebase-onboarding-engineer` only if investigate-codebase is insufficient. |
| **🏠 Implementer** | Mid-build, Task → one specialist for a bounded hard problem (e.g. auth design); Implementer remains owner of patches and branch-gate. |
| **🏠 Test-engineer** | May Task → `test-automation-engineer` / `api-tester` for stack-specific patterns; keep `add-tests` primary. |
| **🏠 Reviewer** | May Task → `code-reviewer` or security slug for high-risk diffs; keep `review-diff` primary. |
| **product-designer** | **Owns design by default** (designer-skills). May Task → one Agency design slug only after documenting pack fit failure. |
| **cursor-config-architect** | Owns `.cursor` layering; Agency pack is an installable specialist layer, not a replacement for REI. |

## Workflow (combined REI + Agency)

1. (Optional) gstack pre-plan / Agency consult for domain depth.  
2. 🏠 **Planner** + **plan-feature** → `plans/` → **user approves**.  
3. 🏠 **Implementer** + **execute-plan** + **branch-gate** (optional Agency Task for hard subproblems).  
4. 🏠 **Test-engineer** → 🏠 **Reviewer** (optional Agency secondary review).  
5. **prepare-pr** → human PR.  

## Safeguards

- Never let an Agency specialist become the sole implementer of a multi-file feature when orchestration is active—unless user opted out of REI for this turn.
- Prefer **one** Agency Task at a time; avoid spawning many specialists in parallel without a clear split.
- If `.cursor/agents/` has no Agency slugs, tell the user to run Agency `install.sh --tool cursor` (selective `--division` recommended).
- Do not convert Agency agents into always-on rules.

## Composition

- Upstream: `.cursor/rules/orchestration.mdc`, `.cursor/rules/agency-integration.mdc`, `.cursor/rules/global.mdc`
- Sibling: `.cursor/skills/gstack-integration/SKILL.md` (release/QA extras)
- Downstream: `.cursor/agents/<slug>.md`, `.cursor/skills/<slug>/`, `/agency`
