# Command Map

Quick guide for choosing the right command in the consolidated REI model.

Routing policy is strict: commands first, then direct subagent route, then direct skill route.

## What should I type?

| If you need to... | Type |
|---|---|
| Build a new feature | `/deliver` |
| Adjust an existing feature | `/deliver` |
| Make a small non-bug improvement | `/deliver` |
| Investigate and fix a bug/regression | `/fix-bug` |
| Design product behavior, UX flows, or screens first | `/design-product` |
| Prepare PR / ship / deploy path | `/release` |
| Get routing help when unsure | `/workflow-guide` |

## Decision hierarchy (strict order)

1. **Commands first**: default to command entry points for all standard workflows.
2. **Subagent route second**: use direct subagent invocation when user asks for role-level control or command abstraction is not preferred.
3. **Direct skill route third**: use direct skill invocation for narrow capability-level workflows or explicit skill preference.

When ambiguous, ask one minimal disambiguation question. If still ambiguous, choose the safest command-first route and state assumptions.

## When to choose direct subagent route

Prefer direct subagent invocation when:

- user explicitly asks for a named agent/subagent
- user wants strict role ownership (planner vs implementer vs reviewer)
- task requires focused handoff without changing command-level scope

Keep REI orchestration and branch policy intact (`Planner -> approval -> Implementer` unless explicitly waived).

## When to choose direct skill route

Prefer direct skill invocation when:

- user explicitly asks for a specific skill
- request is capability-scoped and does not require broad routing
- tactical playbook execution is clearer than command abstraction

Keep recommendations concise and avoid introducing new command variants for one-off flows.

## Lifecycle paths

### New feature

`/design-product` (when UX/product behavior changes) -> `/deliver` -> `/release`

### Feature adjustment

`/deliver` (or `/design-product` first if UX behavior changes materially) -> `/release`

### Small improvement

`/deliver` -> `/release`

### Bug

`/fix-bug` -> `/release` (when fix is ready for PR/ship/deploy path)

### Release

`/release` selects `prepare_pr`, `ship`, or `deploy` path based on explicit intent.

## When /design-product is mandatory

Use `/design-product` before implementation when work changes:

- user-facing flows or navigation
- major interaction patterns/states
- screen-level IA/hierarchy
- cross-device UX behavior

## Security gates checkpoints (summary)

- **Design gate:** Security Design Brief coverage in `/design-product` flows
- **Planning gate:** Security Plan Gate in planning artifacts used by `/deliver` and `/fix-bug`
- **Implementation gate:** secure defaults, boundary validation, least privilege, logging hygiene
- **Testing gate:** include security negative paths/authz checks when applicable
- **Review/release gate:** unresolved HIGH security findings block release path

## Short examples

- "Add a new AI follow-up panel for leads" -> `/design-product`, then `/deliver`
- "Leads API returns 500 after a recent change" -> `/fix-bug`
- "Tweak copy and spacing on a non-critical card" -> `/deliver`
- "Open PR and prepare release checks" -> `/release`
- "Not sure what flow I need" -> `/workflow-guide`
- "I want direct planner control, no command wrapper" -> direct `🏠(REI) Planner` route
- "I only need a targeted debug playbook now" -> direct `debug-issue` skill route
