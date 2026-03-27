---
name: incident
description: Run incident response: triage, mitigate, root cause, document
---

# incident

Mitigate first. Root cause second. Document after.

## Process

**Triage (first 5 minutes)**
1. What is broken? What is the user/system impact? Is it ongoing or already resolved?
2. What changed recently? (deployments, config changes, dependency updates — `git log`, deploy history)
3. Severity: how many users affected, is data at risk, is revenue impacted?

**Investigate**
4. Check logs, metrics, error rates. Find the signal. One hypothesis at a time — don't apply random fixes.
5. Confirm or disprove the hypothesis with evidence before acting.

**Mitigate**
6. Apply the fastest safe fix that stops the bleeding: rollback, feature flag off, rate limit, circuit breaker.
7. Confirm mitigation worked (error rate dropped, service responding).

**Resolve**
8. Apply the proper fix, or create a tracked issue if the full fix is non-trivial and the mitigation holds.

**Document**
9. Write the incident summary.

## Output

```
**Incident Summary**
Impact: [what broke, estimated users affected]
Duration: [start time → resolved time]
Root cause: [one sentence]

Timeline:
- [HH:MM] [event]
- [HH:MM] [event]

Fix: [what was done to resolve]
Follow-up: [what prevents recurrence — linked ticket or action owner]
```

## Rules
- One hypothesis at a time. Shotgun changes under pressure cause new incidents.
- Mitigation ≠ resolution. Mitigation stops the bleeding. Resolution fixes the cause.
- Write the summary while memory is fresh. Don't skip it.
