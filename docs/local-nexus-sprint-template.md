# Local NEXUS-Sprint Template

Use this template when you want to run a **real local NEXUS-Sprint** instead of only copying isolated agent prompts. It turns the repository into a practical operating manual for a feature sprint or MVP slice.

## 1. Best fit

Use this template when you need to:

- build a feature or MVP in roughly 2–6 weeks
- coordinate multiple specialists instead of one generalist
- enforce Dev↔QA loops locally
- keep `strategy/` as the orchestration layer while installing agents into your coding tool

Primary source documents:

- `strategy/QUICKSTART.md`
- `strategy/nexus-strategy.md`
- `strategy/coordination/agent-activation-prompts.md`
- `strategy/coordination/handoff-templates.md`

## 2. Local prerequisites

Before starting the sprint, make sure you have:

1. A working project repo where implementation will happen
2. The specialists installed into your preferred tool
3. This `agency-agents` repository available locally as the strategy source of truth
4. A short feature spec or MVP brief

Recommended supporting assets during execution:

- `specialized/agents-orchestrator.md`
- `testing/testing-evidence-collector.md`
- `testing/testing-reality-checker.md`

## 3. Suggested local folder convention

Inside your target product repo, keep sprint materials in a dedicated folder so the orchestrator, implementation agents, and QA agents all reference the same files.

```text
project-root/
├── docs/
│   └── nexus-sprint/
│       ├── sprint-brief.md
│       ├── sprint-backlog.md
│       ├── architecture-notes.md
│       ├── qa-verdicts/
│       └── handoffs/
├── src/
├── tests/
└── ...
```

Minimum files to create before kickoff:

- `docs/nexus-sprint/sprint-brief.md`
- `docs/nexus-sprint/sprint-backlog.md`
- `docs/nexus-sprint/handoffs/`
- `docs/nexus-sprint/qa-verdicts/`

## 4. Sprint brief template

Create `docs/nexus-sprint/sprint-brief.md` with the following structure:

```md
# Sprint Brief

## Feature / MVP
[What is being built]

## User problem
[What pain point this sprint solves]

## Scope included
- [Item 1]
- [Item 2]
- [Item 3]

## Scope excluded
- [Non-goal 1]
- [Non-goal 2]

## Success criteria
- [Measurable result 1]
- [Measurable result 2]
- [Measurable result 3]

## Constraints
- Timeline: [e.g. 2 weeks]
- Tech constraints: [framework, API, infra]
- Quality constraints: [accessibility, performance, security]
```

Keep this brief short. The sprint should stay narrow enough for `NEXUS-Sprint`, not `NEXUS-Full`.

## 5. Sprint backlog template

Create `docs/nexus-sprint/sprint-backlog.md`:

```md
# Sprint Backlog

## Sprint goal
[One sentence]

## Ordered tasks
1. [Task ID] [Description] [Owner type]
2. [Task ID] [Description] [Owner type]
3. [Task ID] [Description] [Owner type]

## Acceptance criteria by task
### [Task ID]
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

Keep each task small enough to pass through one Dev↔QA loop.

## 6. Orchestrator kickoff prompt

Start with the `Agents Orchestrator` flow from `strategy/coordination/agent-activation-prompts.md` and adapt it like this:

```text
You are the Agents Orchestrator executing the NEXUS pipeline for [PROJECT NAME].

Mode: NEXUS-Sprint
Project specification: docs/nexus-sprint/sprint-brief.md
Current phase: Phase 1 — Strategy & Architecture

NEXUS Protocol:
1. Read the sprint brief thoroughly
2. Read docs/nexus-sprint/sprint-backlog.md
3. Use strategy/playbooks/phase-1-strategy.md through phase-4-hardening.md as the operating playbooks
4. Manage all handoffs using strategy/coordination/handoff-templates.md
5. Enforce Dev↔QA loops for every implementation task
6. Maximum 3 retries per task before escalation
7. Record outputs in docs/nexus-sprint/handoffs/ and docs/nexus-sprint/qa-verdicts/

Do not expand scope beyond the sprint brief.
```

## 7. Recommended sprint roster

A practical baseline roster for local product delivery:

- **Control:** `specialized/agents-orchestrator.md`
- **Planning:** `project-management/project-manager-senior.md`, `product/product-sprint-prioritizer.md`
- **Design / Architecture:** `design/design-ux-architect.md`, `design/design-brand-guardian.md`
- **Implementation:** `engineering/engineering-frontend-developer.md`, `engineering/engineering-backend-architect.md`, `engineering/engineering-devops-automator.md`
- **Quality:** `testing/testing-evidence-collector.md`, `testing/testing-reality-checker.md`, optionally `testing/testing-api-tester.md`

For a UI-heavy sprint, bias toward frontend + UX + Evidence Collector.
For an API-heavy sprint, bias toward backend + API Tester + Reality Checker.

## 8. Phase-by-phase execution pattern

### Phase 1 — Strategy & Architecture
Use:

- `strategy/playbooks/phase-1-strategy.md`
- `design/design-ux-architect.md`
- `engineering/engineering-backend-architect.md`

Outputs:

- clarified scope
- implementation order
- architecture notes in `docs/nexus-sprint/architecture-notes.md`

### Phase 2 — Foundation
Use:

- `strategy/playbooks/phase-2-foundation.md`
- `engineering/engineering-frontend-developer.md`
- `engineering/engineering-devops-automator.md`

Outputs:

- scaffold or foundation changes
- any required design tokens / infra baseline

### Phase 3 — Build
Use:

- `strategy/playbooks/phase-3-build.md`
- implementation specialists for one task at a time
- `testing/testing-evidence-collector.md` after every task

Rule:

- developer implements one task
- Evidence Collector returns PASS or FAIL
- orchestrator decides retry or advance

### Phase 4 — Hardening
Use:

- `strategy/playbooks/phase-4-hardening.md`
- `testing/testing-reality-checker.md`
- optional `testing/testing-api-tester.md` and `testing/testing-performance-benchmarker.md`

Rule:

- treat Reality Checker as the final gate
- do not claim sprint completion without evidence

## 9. PASS / FAIL / escalation operations

Use the templates from `strategy/coordination/handoff-templates.md` exactly as your handoff documents.

Recommended file convention:

```text
docs/nexus-sprint/handoffs/task-01-to-frontend.md
docs/nexus-sprint/qa-verdicts/task-01-pass.md
docs/nexus-sprint/qa-verdicts/task-02-fail-attempt-1.md
docs/nexus-sprint/qa-verdicts/task-02-escalation.md
```

Practical rule set:

- **PASS** → mark task complete and move on
- **FAIL** with attempts remaining → fix only listed issues, then resubmit
- **FAIL** at attempt 3 → create escalation record and let orchestrator re-scope, reassign, or defer

## 10. End-of-sprint checklist

Before calling the sprint complete, confirm:

- [ ] every in-scope task has a QA verdict
- [ ] every failed task has either been fixed or formally deferred
- [ ] Reality Checker has issued a final verdict
- [ ] the sprint brief still matches delivered scope
- [ ] evidence files exist for major claims
- [ ] project-level tests/lint/build checks have been run in the target repo

## 11. Minimal working routine

If you want the shortest possible local routine:

1. Write `sprint-brief.md`
2. Write `sprint-backlog.md`
3. Kick off `Agents Orchestrator` in `NEXUS-Sprint`
4. Use one implementation agent per task
5. Require `Evidence Collector` for each task
6. Require `Reality Checker` before release

That is the smallest loop that still uses the repository as more than a prompt pack.
