# Security gates (stage-appropriate)

Commands and agents enforce these gates at the matching workflow stage. Do not duplicate full lists in rules or thin command wrappers—cross-reference this doc.

## Design (`/design-product`, product-designer)

**Security Design Brief** — data classification, trust boundaries, abuse cases, auth/authz expectations, privacy constraints, security acceptance criteria.

## Planning (Planner, `/fix-bug`, `/deliver`)

**Security Plan Gate** — threat slice, controls mapped to tasks, secret handling, dependency/supply-chain checks, migration safety, security tests.

## Implementation (Implementer, `execute-plan`)

Boundary validation, least privilege, secure defaults, logging hygiene (no sensitive data in logs).

## Testing (Test-engineer, `add-tests`)

Security-negative paths and authz checks where applicable.

## Review (Reviewer, `review-diff`)

Explicit **Security Findings** section; unresolved **HIGH** severity blocks release.

## Cross-references

- `.cursor/commands/deliver.md`, `.cursor/commands/fix-bug.md` — routing only
- `.cursor/agents/planner.md`, `.cursor/agents/implementer.md`, `.cursor/agents/reviewer.md`
