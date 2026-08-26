---
description: SKL - Route product-design work to the correct designer skill category and leaf playbook under .cursor/skills/.
status: active
---

# design-pack (category router)

Load **one** primary mode, then at most one secondary leaf skill when it materially improves output. Leaf skills under `design-research/`, `ux-strategy/`, `ui-design/`, `design-systems/`, `interaction-design/`, `prototyping-testing/`, `design-ops/`, and `designer-toolkit/` are **reference playbooks**—invoke via paths below, not by memorizing the full pack.

## Research

| Skill | Path |
|-------|------|
| Interview synthesis | `.cursor/skills/design-research/summarize-interview/SKILL.md` |
| Affinity diagram | `.cursor/skills/design-research/affinity-diagram/SKILL.md` |
| Persona | `.cursor/skills/design-research/user-persona/SKILL.md` |
| JTBD | `.cursor/skills/design-research/jobs-to-be-done/SKILL.md` |
| Opportunity framing | `.cursor/skills/ux-strategy/opportunity-framework/SKILL.md` |

## Flow

| Skill | Path |
|-------|------|
| Journey map | `.cursor/skills/design-research/journey-map/SKILL.md` |
| User flow diagram | `.cursor/skills/prototyping-testing/user-flow-diagram/SKILL.md` |
| Card sort / IA | `.cursor/skills/design-research/card-sort-analysis/SKILL.md` |

## Screen

| Skill | Path |
|-------|------|
| Layout grid | `.cursor/skills/ui-design/layout-grid/SKILL.md` |
| Visual hierarchy | `.cursor/skills/ui-design/visual-hierarchy/SKILL.md` |
| Typography | `.cursor/skills/ui-design/typography-scale/SKILL.md` |
| Component spec | `.cursor/skills/design-systems/component-spec/SKILL.md` |

## Interaction

| Skill | Path |
|-------|------|
| State machine | `.cursor/skills/interaction-design/state-machine/SKILL.md` |
| Micro-interaction | `.cursor/skills/interaction-design/micro-interaction-spec/SKILL.md` |
| Feedback | `.cursor/skills/interaction-design/feedback-patterns/SKILL.md` |
| Errors | `.cursor/skills/interaction-design/error-handling-ux/SKILL.md` |
| Loading | `.cursor/skills/interaction-design/loading-states/SKILL.md` |

## Validation

| Skill | Path |
|-------|------|
| Usability test plan | `.cursor/skills/design-research/usability-test-plan/SKILL.md` |
| Test scenarios | `.cursor/skills/prototyping-testing/test-scenario/SKILL.md` |
| Accessibility test plan | `.cursor/skills/prototyping-testing/accessibility-test-plan/SKILL.md` |
| A/B test design | `.cursor/skills/prototyping-testing/a-b-test-design/SKILL.md` |

## Handoff

| Skill | Path |
|-------|------|
| Handoff spec | `.cursor/skills/design-ops/handoff-spec/SKILL.md` |
| Design QA checklist | `.cursor/skills/design-ops/design-qa-checklist/SKILL.md` |
| Design rationale | `.cursor/skills/designer-toolkit/design-rationale/SKILL.md` |

## gstack (optional; install via `scripts/install-gstack-cursor-skills.ps1`)

| Skill | Path |
|-------|------|
| Pre-build design rubric | `.cursor/skills/gstack/plan-design-review/SKILL.md` |
| Live visual QA | `.cursor/skills/gstack/design-review/SKILL.md` |
| Design system from scratch | `.cursor/skills/gstack/design-consultation/SKILL.md` |
| Live DX audit | `.cursor/skills/gstack/devex-review/SKILL.md` |
| Ideation | `.cursor/skills/gstack/office-hours/SKILL.md` |
| Strategy review | `.cursor/skills/gstack/plan-ceo-review/SKILL.md` |

gstack code-editing skills: **feature/fix branch only** (`.cursor/skills/branch-gate/SKILL.md`, `gstack-integration/SKILL.md`).

## Selection heuristics

- "Understand users / synthesize" → Research
- "How users move through" → Flow
- Page/screen/component structure → Screen
- States, transitions, errors, loading → Interaction
- "How to test/validate" → Validation
- Engineering-ready delivery → Handoff
- Score design before build → gstack plan-design-review
- Audit running UI → gstack design-review
- Early ideation → gstack office-hours / plan-ceo-review → then Planner for `plans/`

## Agent

**🏠(REI) product-designer** uses this router; parent agents should **Task** to product-designer rather than load the full pack inline.

## Agency design division (not the default)

This pack is the **regular** design path. Do **not** redirect routine work to Agency `ui-designer` / `ux-researcher` / etc.

Escalate to an Agency design slug only when a leaf here cannot cover the ask (brand systems, AI image prompts, inclusive visuals, CRO walkthroughs, finish-gate, whimsy, …). Policy: `.cursor/skills/agency-integration/SKILL.md` § Design — state the fit failure before Task.
