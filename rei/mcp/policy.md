# MCP Policy

## Purpose

Define workspace-level MCP governance: capability boundaries, authorized callers, schema-first execution, and safety defaults.

## Core Rules

- Use MCP only when external capability is required and local repo tools are insufficient.
- Read the MCP tool schema/descriptor before every MCP tool call.
- Keep MCP actions least-privilege and task-scoped.
- Do not auto-approve PRs or auto-merge by default.

## Server Capability Matrix

| Server | Primary capability | Typical use | Write risk |
| --- | --- | --- | --- |
| `cursor-ide-browser` | Browser automation and UI verification | Navigate pages, snapshots, screenshots, interaction validation | Medium |
| `user-real-estate-crm-service-manager` | Local service diagnostics/control | Run diagnostics, start/stop/status for local app services | Medium |
| `user-frontend-playwright` | Browser test automation | Targeted runtime UI checks and evidence capture | Medium |
| `user-mongodb` | Database inspection and operations | Data checks and controlled DB operations when required | High |
| `user-git` | Git host-independent operations | Branch/PR-adjacent git workflows via MCP if required | Medium |
| `user-github` | GitHub PR/review/check operations | PR creation/updates, review context, CI/check gating | High |

## Authorized Callers

- **Agents:** call MCP only within their boundary responsibilities and by referencing canonical skills.
  - `🏠(REI) Researcher`: discovery-only MCP usage when local evidence is insufficient.
  - `🏠(REI) Implementer`: MCP usage for implementation validation or required external actions.
  - `🏠(REI) Test-engineer`: MCP usage for targeted runtime test validation.
  - `🏠(REI) Reviewer`: MCP usage for runtime verification and GitHub review context.
  - `🏠(REI) Planner`: MCP usage is exceptional and should remain read-focused.
- **Skills:** MCP operation details are canonical in `.cursor/skills/github-mcp/SKILL.md` and repo-specific testing/review skills.
- **Commands/Hooks:** must remain deterministic and scoped; no broad or interactive MCP automation.

## Schema-First Requirement

1. Identify the MCP server and tool.
2. Read the local descriptor schema before invocation.
3. Validate required arguments and allowed fields against schema.
4. Call the tool with only supported arguments.
5. Record key outputs and blockers in task reporting.

## Authentication and Failure Handling

- If a server exposes `mcp_auth`, authenticate before operational calls.
- Authenticate one server at a time.
- On auth failure, permission denial, or schema mismatch: stop writes, report blocker, and request user direction.
- Do not retry destructive or state-changing operations without a new hypothesis and confirmation.

## Least-Privilege and Safety Defaults

- Prefer read operations before write operations.
- Scope write actions to the minimum target (single repo, PR, thread, service, or dataset).
- For GitHub:
  - Approval is manual human-owned unless explicitly requested.
  - Merge is manual human-owned unless explicitly requested.
  - Do not force push or bypass protections unless explicitly requested.
- For database/service operations:
  - Avoid destructive actions unless explicitly requested and confirmed.
  - Prefer reversible or read-only checks first.
