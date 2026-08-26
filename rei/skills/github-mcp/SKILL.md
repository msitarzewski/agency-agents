---
description: SKL - Perform GitHub MCP operations for PR lifecycle, checks, and review threads within policy boundaries.
---

# github-mcp

## Purpose

Safe workflow for GitHub operations via **`user-github`** MCP using supported tool names and argument shapes only.

## When to use

Create/update/inspect PRs; triage reviews and CI; merge-readiness (merge only when user explicitly requests).

## Required context

`owner`, `repo`, `head`, `base` (or branch to publish); intended action; merge policy; issue/reviewer requirements.

## Workflow

1. **Auth:** `get_me` on `user-github`; read tool schemas before each call.
2. **State:** `list_branches`, `list_pull_requests` / `search_pull_requests`, `list_commits`.
3. **Execute** one primary action from **`.cursor/docs/github-mcp-actions.md`**.
4. **Guardrails** before writes: re-verify repo, branch, PR number; merge requires checks + approvals.
5. **Return:** `action`, `inputs`, `result`, `artifacts`, `next_steps`, `errors`.

## Expected deliverable

Structured report with PR/check URLs and blockers. ~95% done: one-click compare link to `DEV` (or multi-repo list).

## Safeguards

No force-push unless requested. No merge without gates. No auto-approve/auto-merge unless user explicitly requests in this conversation. Idempotent PR creation. Narrow scope: one primary action per invocation.

## Composition

`branch-gate` before local work feeding PRs; `prepare-pr` for narratives; `review-diff` for finding fixes.

## Canonical reference

Full action catalog, thread IDs, pagination, and PR templates: **`.cursor/docs/github-mcp-actions.md`**. On conflict, follow this skill and live MCP schemas.
