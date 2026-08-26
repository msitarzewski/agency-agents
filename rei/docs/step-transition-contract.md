# Step-transition messaging contract

Enforced at significant workflow boundaries (handoffs, blockers, approval gates, waiting states). Agents and commands must surface transition state in this order:

1. **Status:** `Completed`, `Blocked`, `In Progress`, or `Waiting on User`
2. **Reason:** concise cause or current condition
3. **Next required action:** exact user action in imperative form (or explicit autonomous next step)
4. **Step complete / current state** details for workflow handoffs

## Required labels

- `Status: <Completed|Blocked|In Progress|Waiting on User>`
- `Reason: <concise reason>`
- `Step complete: <completed step>`
- `Current state: <ready|blocked: reason>`
- `Next required action: <exact user reply/action>`

When multiple valid paths exist, `Next required action` must present concrete options (`Option A …` / `Option B …`), not vague "how should we proceed?" prompts.

## Approval gates (mandatory blockers)

`Next required action` must explicitly ask for one of:

- `Reply "approve plan <path>" to continue with Implementer.`
- `Reply "waive plan approval" to continue without separate approval.`

Do not end a gated step with only "continue/proceed/go ahead" phrasing. The exact user action must appear in the same response that reports step completion.

## Cross-references

- Routing defaults: `.cursor/rules/orchestration.mdc`
- Planner close-out: `.cursor/agents/planner.md`
- Command entrypoints: `.cursor/commands/fix-bug.md`, `.cursor/commands/deliver.md`
