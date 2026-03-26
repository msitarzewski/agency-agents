---
name: security-scan
description: Audit codebase for security vulnerabilities across the attack surface
---

# security-scan

Find real, exploitable security issues. Not theoretical — practical attack paths.

## Process
1. Map the attack surface: HTTP routes, CLI args, file inputs, webhooks, env var handling, auth middleware.
2. Check each entry point for:
   - **Injection**: SQL (string concatenation), command injection (exec/shell with user input), template injection, path traversal (`../`)
   - **Auth**: missing authentication checks, broken authorisation (user A accessing user B's data), privilege escalation paths
   - **Secrets**: hardcoded API keys, passwords, tokens in source or committed config files
   - **Input validation**: unvalidated user input reaching dangerous sinks, type coercion bugs, missing length limits
3. Check for insecure patterns regardless of entry point:
   - `eval()` or `Function()` with user data
   - Deserialisation of untrusted data
   - CORS wildcard (`*`) on authenticated endpoints
   - Missing CSRF protection on state-changing endpoints
   - Outdated dependencies with known CVEs (`npm audit` / `pip audit` / `bundle audit`)
4. Check secrets in git history if `.git` is accessible.

## Output
Findings grouped by severity:

**Critical** — direct exploitation path, fix immediately
**High** — likely exploitable with moderate effort
**Medium** — exploitable under specific conditions
**Low** — defence-in-depth improvements

Each finding: location (file:line) — vulnerability type — attack scenario (one sentence) — fix.

## Rules
- Only report findings with a realistic attack path. No theoretical issues.
- Prioritise. Critical and High are what matter before shipping.
- If a finding requires insider access or physical access to exploit, classify it Low.
