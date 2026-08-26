---
description: CMD - ⚡(REI) Route release intent to prepare-pr or explicit gstack ship/deploy workflows with branch and security gate checks.
---

CMD - Consolidated release gateway for PR/ship/deploy path selection.

CMD - ⚡(REI) /release

Purpose: Deterministic release gateway that selects the correct PR/ship/deploy path without duplicating skill playbooks.

## Required inputs

- target repositories and branches
- desired action (`prepare_pr`, `ship`, `deploy`, or combined)
- environment target (integration/staging/production)

If required inputs are missing, ask concise clarifying questions before acting.

## Default path

- Preferred flow is REI `prepare-pr` style PR preparation and manual human approval/merge on protected branches.
- Merges/deploys remain user-owned unless explicitly requested.

## Path selection

1. **PR only / standard release prep**
   - Route to `.cursor/skills/prepare-pr/SKILL.md`
2. **Explicit gstack ship request**
   - Route through `.cursor/skills/gstack-integration/SKILL.md` to gstack `ship`
   - Only when user explicitly requests ship automation
3. **Post-merge deploy verification**
   - Route through `.cursor/skills/gstack-integration/SKILL.md` to gstack `land-and-deploy` (and optional `canary`)

## Security and safety gates (mandatory)

- protected branch policy from `.cursor/rules/global.mdc` always applies
- confirm release target and auth/authz expectations before ship/deploy
- block release path if unresolved HIGH security findings exist from review
- require explicit confirmation for production-impacting deploy actions

## Notes

- Keep this command as a thin routing contract only.
- For feature/adjustment implementation flow, use `/deliver`.
- For bug-fix lifecycle, use `/fix-bug`.

## Step-finish messaging (required)

When `/release` selects a path, always close with explicit transition messaging per `.cursor/docs/step-transition-contract.md`:

- `Step complete: release path selected`
- `Current state: ready` (or `blocked: <reason>`)
- `Next required action: <exact command/action>`
