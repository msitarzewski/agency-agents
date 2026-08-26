# GitHub MCP action catalog (`user-github`)

Canonical mapping for agents using `.cursor/skills/github-mcp/SKILL.md`. Read MCP tool schemas before each call.

## Actions

| Action | Tools | Notes |
|--------|-------|-------|
| `authenticate_github` | `get_me` | Session/token probe |
| `inspect_repo_state` | `list_branches`, `list_pull_requests`, `search_pull_requests`, `list_commits` | Branch + PR linkage |
| `create_pull_request` | `create_pull_request` | Required: `owner`, `repo`, `title`, `head`, `base`. Optional: `body`, `draft`, `maintainer_can_modify` |
| `update_pull_request` | `update_pull_request` | Required: `owner`, `repo`, `pullNumber`. Updates: `title`, `body`, `base`, `draft`, `state`, `reviewers`, `maintainer_can_modify` |
| `fetch_pr_context` | `pull_request_read` | Methods: `get`, `get_diff`, `get_files`, `get_reviews`, `get_review_comments`, `get_comments`, `get_status`, `get_check_runs` |
| `triage_review_feedback` | `pull_request_read` | Unresolved threads/comments |
| `manage_review_threads` | `pull_request_review_write`, `add_reply_to_pull_request_comment`, `add_comment_to_pending_review` | `resolve_thread` / `unresolve_thread` via `threadId` |
| `submit_review_decision` | `pull_request_review_write` | `create` (optional `event`), `submit_pending` (`APPROVE`/`REQUEST_CHANGES`/`COMMENT`), `delete_pending` |
| `refresh_pr_branch` | `update_pull_request_branch` | Sync with base |
| `gate_merge_readiness` | `pull_request_read` | Checks, reviews, threads |
| `merge_pull_request` | `merge_pull_request` | Required: `owner`, `repo`, `pullNumber`. Optional: `merge_method` (`merge`/`squash`/`rebase`), `commit_title`, `commit_message`. User-explicit only |
| `link_work_items` | `issue_read`, `issue_write`, `add_issue_comment`, `sub_issue_write`, `search_issues`, `list_issues` | Issue sync |

## Pagination

- Many REST-style tools: `page` / `perPage`.
- `list_issues`: `after` cursor where supported.
- When filtering PRs by author, use `search_pull_requests`, not `list_pull_requests`.

## Safeguards

- Never force-push unless user explicitly requests.
- Never merge without required checks/approvals.
- No `APPROVE` or `merge_pull_request` unless user explicitly requests in this conversation.
- `threadId` from `pull_request_read` (`get_review_comments`).
- `update_pull_request` does not accept labels/assignees.
- Human governance: PR approval and merge are manual unless explicitly requested.

## PR link template

`https://github.com/<owner>/<repo>/compare/DEV...<head>?expand=1`

## PR action block (single repo)

Use when coding is ~95% done:

```text
## Next Action
- Create PR to DEV now: [Open PR to DEV](https://github.com/<owner>/<repo>/compare/DEV...<head>?expand=1)

## Governance
- PR approval is manual (human-only).
- PR merge is manual (human-only).
- Agents do not auto-approve or auto-merge unless explicitly requested in this conversation.
```

## Multi-repo PR list

```text
## Next Action
### Multi-Repo PR List (target: DEV)
- [Open backend PR to DEV](https://github.com/<owner>/<backend-repo>/compare/DEV...<head>?expand=1)
- [Open frontend PR to DEV](https://github.com/<owner>/<frontend-repo>/compare/DEV...<head>?expand=1)

## Governance
- PR approval is manual (human-only).
- PR merge is manual (human-only).
- Agents do not auto-approve or auto-merge unless explicitly requested in this conversation.
```
