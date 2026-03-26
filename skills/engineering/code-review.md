---
name: code-review
description: Review changed files for bugs, security issues, and maintainability
---

# code-review

Review code changes and produce actionable findings, grouped by severity.

## Process
1. Run `git diff HEAD` (or `git diff HEAD~1` if nothing staged). If no git context, review the files the user specifies.
2. For each changed file, check:
   - **Correctness**: logic errors, off-by-one, wrong operator, unintended mutation
   - **Security**: injection (SQL, command, template), unvalidated input, hardcoded secrets, missing auth checks, path traversal
   - **Error handling**: uncaught exceptions, silent failures, missing null/undefined guards
   - **Performance**: N+1 queries, blocking calls that could be async, unnecessary re-computation
   - **Dead code**: unused imports, unreachable branches, leftover debug statements
3. Check cross-file concerns: broken module contracts, missing DB migrations, test coverage gaps for changed logic.

## Output
Group by severity:

**Critical** — must fix before merge (bugs that corrupt data, security vulnerabilities)
**Major** — should fix (correctness issues, missing error handling)
**Minor** — consider fixing (performance, dead code, clarity)

Each finding: `file:line` — what's wrong — how to fix it (one line).

If no issues found, say so plainly.

## Rules
- Only flag real issues. Do not invent problems to appear thorough.
- Do not suggest refactors outside the changed scope unless directly related to a bug.
- If a finding is uncertain, say "possible issue" not "issue".
