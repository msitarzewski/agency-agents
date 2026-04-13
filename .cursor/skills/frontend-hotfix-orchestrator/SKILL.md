---
name: frontend-hotfix-orchestrator
description: Orchestrates targeted, minimal frontend changes (hotfixes, small UI tweaks, or bug fixes) in an existing codebase without triggering a full QA cycle. Use when the user asks for a small fix or minimal change.
---

# Frontend Hotfix Orchestration

Use this skill when the task is to make a **targeted, minimal change** (hotfix, small UI tweak, or bug fix) in an existing frontend project. Unlike the full feature orchestration, this flow minimizes overhead and prevents scope creep.

## Goal

Move from understanding to implementation to proof to review with the smallest useful loop. Optimize for speed and minimal diffs without skipping validation.

## Subagent Model

Treat each stage as its own focused pass.

- Do not start implementation until onboarding output is explicit.
- Do not start final acceptance until evidence is collected.
- Do not treat evidence as a substitute for review.
- When the feature needs extra validation, run independent checks in parallel after implementation.

## Weak-Model Mode & Minimal Handoff

When downstream subagents are not very capable, make the job easier by reducing ambiguity and reasoning depth.

- Give each subagent exactly one job.
- Keep handoffs short and literal.
- Use concrete file paths, exact constraints, and explicit done criteria.
- Prefer `find`, `edit`, `verify`, and `list` over vague verbs like `improve` or `analyze`.
- Never mix discovery, implementation, and review in one pass.
- Ask for at most 3 findings, 3 risks, or 3 recommendations per agent.
- If something is missing, the agent must return `BLOCKED` with one precise question instead of guessing.

### Handoff Packet

Use this structure when calling a subagent:

```markdown
Role: [Role Name]
Goal: [1-sentence description of the targeted change]
Files: [Exact paths if known, or "discover first"]
Constraints: DO NOT refactor. Make the minimal possible change.
Output format: 
Result: [summary]
Evidence: [files changed / proof]
Risks: [max 1]
Blocked: [reason or None]
```

## Default Orchestration

1. **Codebase Onboarding Engineer**
   - **Goal:** Quickly locate the exact file(s) and lines that need to be changed.
   - **Output:** A strict list of 1-3 files and the specific context for the change.

2. **Minimal Change Engineer**
   - **Goal:** Implement the requested change with the absolute minimum number of lines.
   - **Why not Frontend Developer?** The Frontend Developer agent might try to refactor, add new patterns, or over-engineer. The Minimal Change Engineer is explicitly instructed to refuse scope creep and only fix what was asked.
   - **Output:** A minimal diff touching only the necessary lines.

3. **Evidence Collector**
   - **Goal:** Verify that the specific bug is fixed or the specific UI element is changed.
   - **Output:** Screenshots or console output proving the targeted change works.

4. **Code Reviewer**
   - **Goal:** Perform a quick sanity check on the minimal diff to ensure no obvious regressions or syntax errors were introduced.
   - **Output:** PASS or a short list of blockers.

*(Note: We skip the `Reality Checker` and `Product Manager` for targeted changes, as the acceptance criteria for a hotfix are usually binary and self-evident).*

## Example Flow

For a targeted hotfix in an existing project:

1. Map the codebase to find the exact file and line.
2. Implement the minimal change.
3. Collect proof that the bug is fixed.
4. Review the minimal diff.