---
name: frontend-feature-orchestrator
description: Orchestrates frontend feature delivery in an existing codebase through repository onboarding, implementation, evidence capture, reality checks, and code review. Use when the user asks to add or change frontend functionality and wants a repeatable Cursor workflow.
---

# Frontend Feature Orchestrator

Use this skill when the task is to implement a new frontend feature or change an existing one in a live codebase and you want a fast, repeatable delivery loop.

## Goal

Move from understanding to implementation to proof to review with the smallest useful loop. Optimize for speed without skipping validation.

## Subagent Model

Treat each stage as its own focused pass.

- Do not start implementation until onboarding output is explicit.
- Do not start final acceptance until evidence is collected.
- Do not treat evidence as a substitute for review.
- When the feature needs extra validation, run independent checks in parallel after implementation:
  - `Evidence Collector`
  - `Accessibility Auditor`
  - `API Tester`

## Weak-Model Mode

When downstream subagents are not very capable, make the job easier by reducing ambiguity and reasoning depth.

- Give each subagent exactly one job.
- Keep handoffs short and literal.
- Use concrete file paths, exact constraints, and explicit done criteria.
- Prefer `find`, `edit`, `verify`, and `list` over vague verbs like `improve` or `analyze`.
- Never mix discovery, implementation, and review in one pass.
- Ask for at most 3 findings, 3 risks, or 3 recommendations per agent.
- If something is missing, the agent must return `BLOCKED` with one precise question instead of guessing.
- Keep parallel work only for independent read-only checks.

### Handoff Packet

Use this structure when calling a subagent:

```markdown
Role: [one role only]
Goal: [one sentence]
Scope: [in scope / out of scope]
Files: [exact paths or "discover first"]
Known facts: [3-5 bullets]
Constraints: [stack, patterns, limits]
Output format: [exact shape]
Stop if: [what should trigger BLOCKED]
```

### Output Contract

Require a fixed response shape from every subagent:

```markdown
Result:
Evidence:
Risks:
Blocked:
Next:
```

If the task is simple, accept short bullets. If the task is unclear, force the agent to return `Blocked` before it does anything else.

## Default Orchestration

1. **Codebase Onboarding Engineer**
   - Inspect the repo structure, entry points, related modules, and local conventions.
   - Output:
     - affected files
     - implementation constraints
     - unknowns and risks
     - a short implementation plan

2. **Frontend Developer**
   - Implement the feature in the smallest shippable slice.
   - Follow the plan, reuse existing patterns, and keep the change focused.
   - Output:
     - what changed
     - files touched
     - tests or checks added

3. **Evidence Collector**
   - Gather facts after implementation.
   - Collect screenshots, console output, test results, and any observable proof.
   - Output:
     - factual results only
     - what is working
     - what is still failing

4. **Reality Checker**
   - Compare the evidence against the requested behavior.
   - Decide PASS / FAIL based on the actual result, not optimism.
   - Output:
     - verdict
     - missing acceptance criteria
     - blockers if any

5. **Code Reviewer**
   - Review the diff for correctness, maintainability, regression risk, and test coverage.
   - Output:
     - blockers
     - suggestions
     - anything that should be fixed before merge

## Final Validation Loop

After fixes, run only the roles that can be affected by the new changes:

1. **Evidence Collector**
2. **Reality Checker**
3. **Code Reviewer**

Do not repeat the full loop unless the implementation changed in a way that affects understanding or scope.

## Optional Roles

Add these only when the task needs them:

- **Product Manager**: the scope is vague, success criteria are missing, or the feature needs tighter definition.
- **Accessibility Auditor**: the feature adds forms, modals, tabs, keyboard flows, or other interactive UI.
- **API Tester**: the frontend depends on a new or changed API contract.

## Rules

- Keep `Codebase Onboarding Engineer` at the start of the cycle.
- Keep `Frontend Developer` as the execution role.
- Use `Evidence Collector` for facts, not judgment.
- Use `Reality Checker` for acceptance, not code quality.
- Use `Code Reviewer` for code quality, not product acceptance.
- Do not run the final QA loop twice on unchanged code.
- If review finds issues, return only to the roles needed to fix them.
- If onboarding cannot identify safe edit points, stop and ask for clarification before coding.

## Recommended Output Format

When following this skill, report progress in this shape:

```markdown
## Orchestration Plan
- Onboarding: ...
- Implementation: ...
- Evidence: ...
- Reality check: ...
- Review: ...

## Current Status
- What is done:
- What is pending:
- What is blocked:
```

## Example Flow

For a new frontend feature in an existing project:

1. Map the codebase.
2. Implement the feature.
3. Collect proof.
4. Validate against requirements.
5. Review the diff.
6. Fix only what failed.
7. Re-run evidence, reality check, and review.
