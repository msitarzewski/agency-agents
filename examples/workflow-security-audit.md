# Multi-Agent Workflow: Security Audit

> An end-to-end security audit using The Agency's security division. From kickoff through remediation tracking, coordinated across pen-test, appsec, cloud, and threat-detection agents.

## The Scenario

You're the security lead at a 200-person SaaS company. The board has asked for an independent security review before Series C diligence. You have three weeks. The product is a multi-tenant Node.js + Postgres app on AWS, with a React SPA frontend, a few internal Go services, and a Slack-bot integration. The codebase has not had a formal security review in 18 months.

The goal is not a 200-page report. The goal is a credible, evidence-based answer to the diligence question: "Is this product safe to bet on?" That means a written threat model, a prioritized findings list with CVSS scores, a remediation tracker, a re-test report, and a board-ready summary.

## Agent Team

| Agent | Role in this workflow |
|-------|----------------------|
| Senior SecOps Engineer | Initial threat-model kickoff, sets scope and rules of engagement |
| Application Security Engineer | Code-level SAST, dependency review, secrets scanning |
| Cloud Security Architect | AWS configuration review, IAM, network policy, S3/CloudFront audit |
| Penetration Tester | Authorized external attack simulation, exploit chain development |
| Threat Detection Engineer | SIEM rule gaps, ATT&CK coverage assessment |
| Security Architect | Threat model synthesis, architecture-level findings |
| Reality Checker | Final certification that findings are remediated |
| Incident Responder | Pre-positioned for findings that turn into active incidents |

## The Workflow

### Week 1: Threat model and code-level review

**Step 1 — Activate Senior SecOps Engineer**

```
Activate Senior SecOps Engineer.

Audit target: 200-person SaaS, multi-tenant Node.js + Postgres on AWS.
Engagement: 3 weeks, independent review for Series C diligence.
Scope: production code, AWS account, third-party integrations (Slack, Stripe, Datadog).

Produce a one-page threat model and a written rules-of-engagement that the
pen-tester and the appsec engineer will work within. Define the out-of-scope
list (employee devices, the production customer data itself, third-party
SaaS we don't control).
```

**Step 2 — Activate Application Security Engineer (in parallel)**

```
Activate Application Security Engineer.

Target: same Node.js + Postgres SaaS, AWS-hosted. Codebase has 200+ services
across 4 monorepos.

Run:
1. SAST across the Node.js services — focus on auth, session, crypto, and
   tenant-isolation code paths
2. Dependency review — flag any package with a known critical CVE
3. Secrets scan across all repos — hardcoded keys, .env files committed
   by mistake, long-lived AWS access keys
4. Threat-model-to-code mapping: for each threat in the SecOps engineer's
   model, identify the implementing file and quote the relevant lines

Output: a per-finding report with file:line references and CVSS v3.1 scores.
```

**Step 3 — Activate Cloud Security Architect (in parallel)**

```
Activate Cloud Security Architect.

Target AWS account: production only. Out of scope: dev and staging.

Audit:
1. IAM: identify overly broad policies, unused access keys, cross-account
   trust relationships
2. Network: VPC flow logs, security group rules, public subnets, NACLs
3. S3 / CloudFront: public buckets, missing encryption, broken access
   policies, no versioning
4. RDS: encryption at rest, automated backups, public accessibility
5. Secrets Manager: rotation policies, who can read secrets

Output: a cloud-config findings list with AWS CLI commands that reproduce
each issue, plus the recommended remediation.
```

### Week 2: Authorized pen test and threat detection gap

**Step 4 — Activate Penetration Tester**

```
Activate Penetration Tester.

Engagement: 3 weeks, in line with the rules-of-engagement from week 1.
Authorized: yes. Scope: production app + AWS account.

Goals:
1. Attempt at least 3 cross-tenant data access scenarios
2. Attempt to escalate from a low-privilege user to admin
3. Attempt to extract customer PII via the public API surface
4. Build a reproducible exploit chain for any successful compromise

For each successful attack, document:
- The preconditions (what access did the attacker start with)
- The full chain (each step, with the request/response that worked)
- The blast radius (how much data could be exfiltrated)
- The detection signal (would our SIEM have caught this?)

Output: an exploit-chain document. Reality check the chain yourself —
any chain that doesn't survive a second-pass walk-through is not
reportable.
```

**Step 5 — Activate Threat Detection Engineer (in parallel)**

```
Activate Threat Detection Engineer.

Target SIEM: Datadog. Existing detections: 47 rules, last reviewed 14
months ago.

Audit:
1. Map the 47 existing rules to MITRE ATT&CK. Identify uncovered
   techniques, especially in Initial Access, Persistence, and
   Exfiltration.
2. For each technique used in the pen-tester's exploit chain, verify
   that a detection rule exists and fires on the test traffic.
3. Identify high-noise rules that get tuned out, and propose
   refactors.
4. Document the mean-time-to-detect (MTTD) for the last 3 simulated
   incidents.

Output: a SIEM coverage matrix (technique x rule x MTTD) and a
prioritized backlog of new rules to write.
```

### Week 3: Synthesis, remediation, and certification

**Step 6 — Activate Security Architect**

```
Activate Security Architect.

Inputs: the SecOps threat model, the AppSec findings, the Cloud config
findings, the pen-tester's exploit chains, the SIEM coverage matrix.

Produce:
1. A unified findings list, deduplicated across all input sources,
   sorted by (CVSS score, exploitability, blast radius)
2. A remediation plan: for each finding, who fixes it, by when, and
   how to verify
3. A board-ready 1-page summary: top 5 risks, top 5 wins, residual
   risk posture
4. Architecture-level findings that don't fit in a single repo or
   account (e.g., "we have 6 places that implement session validation,
   each slightly different")
```

**Step 7 — Open the remediation tracker**

Create a single tracking issue per finding. Use a consistent template:
- CVSS v3.1 base score
- Affected services / accounts
- Linked finding report
- Owner (team or named individual)
- Target fix date
- Verification criteria (e.g., "this SAST rule passes on a clean run")

**Step 8 — Activate Reality Checker (after fixes land)**

```
Activate Reality Checker.

For each finding marked "fixed" in the remediation tracker:
1. Verify the fix is in the merged main branch
2. Re-run the original reproduction (e.g., the SAST rule, the AWS CLI
   command that demonstrated the misconfig, the exploit-chain endpoint)
3. Verify the fix doesn't regress other behavior

Output: a per-finding certification ("fixed" or "not fixed") with
evidence.
```

**Step 9 — Activate Incident Responder (if anything escalated)**

If the pen test turned up an actual breach, or if a fix attempt
introduced a new outage, activate the Incident Responder in parallel
with the Reality Checker. The audit is a good time to practice
incident response on a real trigger.

## What good looks like

A successful 3-week audit produces:

- **A written threat model** that names the realistic attacker profiles and
  the most-exposed assets.
- **A prioritized findings list** with CVSS v3.1 scores, file/line references
  for code findings, AWS CLI repro commands for cloud findings, and full
  exploit chains for successful pen-test attacks.
- **A remediation tracker** with named owners, target dates, and verification
  criteria for every finding.
- **A re-test report** confirming the fixes actually work — not just that
  someone said they merged a PR.
- **A board-ready 1-page summary** that says, in language the board understands,
  what the residual risk posture is and what they should track over the next
  two quarters.

The agents in this workflow are not a substitute for experienced security
judgment. They are multipliers: they cover the work systematically, so the
human security lead can focus on the calls that actually require experience
— the ones where the threat model is genuinely uncertain, or the
remediation tradeoff involves business risk.

## See also

- `examples/workflow-startup-mvp.md` — for a multi-agent workflow that runs
  across the entire engineering division
- `examples/workflow-with-memory.md` — for the same kind of audit
  coordinated through an MCP memory server instead of manual handoffs
- `security/security-architect.md` — the agent that synthesizes the
  audit's findings into architecture-level recommendations
