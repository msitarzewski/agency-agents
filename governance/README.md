# 🏛️ Governance

Specialists for **policy-enforced, cryptographically-audited AI agent systems**.

As autonomous agents take on work that affects money, safety, and rights,
they need governance primitives: declarative policies evaluated before each
action, and tamper-evident records of every decision made.

The agents in this category are the execution-level operators who verify
individual artifacts day-to-day. They pair naturally with
[Agentic Identity & Trust Architect](../specialized/agentic-identity-trust.md)
(who designs the system) and
[Compliance Auditor](../specialized/compliance-auditor.md)
(who maps controls to frameworks like SOC 2 / ISO 27001).

## Agents in this Category

| Agent | Specialty |
|-------|-----------|
| [Receipt Auditor](./receipt-auditor.md) 🔍 | Verifies Ed25519-signed decision receipt chains. Walks hash chains, detects tampering, explains failures. |
| [Cedar Policy Reviewer](./cedar-policy-reviewer.md) ⚖️ | Reviews Cedar authorization policies for agent tool calls. Catches over-permissive rules and missing deny tripwires. |

## When to Use

Activate agents from this category when you need to:

- Deploy an autonomous agent in a regulated domain (finance, healthcare, research)
- Prove, to a third party, what an agent actually did and why
- Write or audit authorization policies for Claude Code, MCP gateways, or Microsoft Agent Governance Toolkit
- Diagnose signature failures or chain breaks in receipt logs
- Build compliance evidence from agent actions without running a central audit service

## Standards These Agents Work With

- **Cedar** — AWS's open authorization policy language ([cedarpolicy.com](https://www.cedarpolicy.com/))
- **Ed25519** — RFC 8032 digital signatures
- **JCS** — RFC 8785 JSON canonicalization
- **IETF draft-farley-acta-signed-receipts** — signed decision receipt wire format

## Related Divisions

- [`specialized/`](../specialized/) — broader catalog, including Identity & Trust Architect and Compliance Auditor
- [`engineering/`](../engineering/) — DevOps and incident response specialists who operate alongside governance tooling
