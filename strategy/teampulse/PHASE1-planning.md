# TeamPulse — Phase 1 Planning

NEXUS-Sprint mode. Skip Phase 0 (market validated). No production code in this artifact.

## Architecture outline (daily job + DB + idempotency + batching + failures)

**Goal:** Daily at a fixed time (business timezone defines "today"), scan PostgreSQL for tasks where `due_date < today_start` and `status != done`, aggregate by **assignee**, send **one** SMTP summary email per assignee.

### Components

| Layer | Responsibility |
|-------|----------------|
| **Scheduler** | Cron / K8s CronJob / internal authenticated endpoint. Each run has a `run_id` (UUID or `(date, job_name)`). |
| **Job module (Node.js)** | Load config (DB, SMTP, timezone, from/reply-to, feature flag). Query → aggregate → render → send. Structured logging; avoid PII in info-level logs or redact. |
| **PostgreSQL** | Filter: `due_date < :today_start` AND `status NOT IN ('done', …)`. Skip null assignee in MVP (metric only). Aggregate by `assignee_id`. Index: `(status, due_date)` or partial index as needed. |

### Idempotency

- **Granularity:** At most **one successful send per assignee per calendar day** (business timezone).
- **Storage:** Table `digest_sent` with unique `(digest_date, assignee_id, job_name)`; `INSERT` before send, skip on conflict. Or outbox with `(run_id, assignee_id, status)`.
- **Re-run same day:** Skip already-sent assignees; retry only failed assignees (no duplicate mail).

### Email batching

- One email per assignee; list tasks inside (id, title, due_date, project/link).
- Optional cap on rows per email with "N more" + link if product supports it.
- Sequential SMTP with configurable delay/concurrency; optional audit BCC if policy allows.

### Failure handling

| Failure | Behavior |
|---------|----------|
| Single recipient | Log error; retry up to **3 times** with backoff; then alert, continue others. |
| Whole DB | Job `failed`; no bulk success marks; retry on next schedule or manual run. |
| SMTP auth/config | Fail fast + high-priority alert. |

**Observability:** Counts for scanned tasks, recipients, success/fail/skip (idempotent). Analytics Reporter defines baseline metrics at launch.

---

## Sprint backlog

| ID | User story | Owner agent | Definition of Done | Suggested QA agent |
|----|------------|-------------|--------------------|--------------------|
| TP-01 | Freeze MVP scope and non-goals (timezone, terminal statuses, empty assignee). | Senior Project Manager | One-page acceptance criteria, non-goals, open questions owned; aligned with architecture. | Reality Checker |
| TP-02 | Ordered Phase 2–4 backlog with dependencies for Dev↔QA loops. | Sprint Prioritizer | Prioritized backlog, blockers visible, retry/escalation rules documented. | Evidence Collector |
| TP-03 | ADR for schema, query/index, idempotency store, failure/replay. | Backend Architect | ADR + query sketch + idempotency keys + failure strategy; Reality Checker readable. | Reality Checker |
| TP-04 | Clear email structure (grouping, fields, row cap). | UX Architect | Wireframe-level outline (text/HTML), mobile-readable notes, field alignment with backend. | Evidence Collector |
| TP-05 | Subject/signature/tone per brand guidelines. | Brand Guardian | Subject template, footer, banned-word checklist; no conflict with UX outline. | Evidence Collector |
| TP-06 | Implement scan, aggregate, render, SMTP send with per-recipient retry cap. | Backend Architect | Review passed, core unit tests, staging run (after explicit "开始实现"). | API Tester |
| TP-07 | Daily schedule, secrets/config parity across envs, observability. | DevOps Automator | Cron/CronJob docs, alerts, rollback steps aligned with job timeout/retry. | API Tester |
| TP-08 | Decide minimal admin surface (env/flag only vs UI). | Senior Project Manager, Sprint Prioritizer | Written decision: no UI or Frontend Developer story created; aligned with TP-01. | Reality Checker |
| TP-09 | Contract and failure-scenario test cases for job/API. | API Tester | Case list: empty result, partial SMTP failure, idempotency conflict, DB down; evidence links. | Evidence Collector |
| TP-10 | Post-launch metrics baseline (delivery/failure rates). | Analytics Reporter | Metric definitions, collection points, first-week dashboard/log convention. | Reality Checker |

---

## Phase 1 → Phase 2 gate checklist

Copy and tick manually:

```markdown
## Phase 1 → Phase 2 gate (Architecture & Scope Freeze)

- [ ] MVP scope and non-goals fixed in writing; consistent with skipping Phase 0
- [ ] "Today" boundary (business timezone) and terminal `status` set documented
- [ ] Empty assignee and large-list (truncate/cap) behavior decided
- [ ] PostgreSQL filter/aggregate query draft finalized; index/full-scan risk resolved
- [ ] Idempotency strategy chosen (e.g. assignee + digest_date) and in ADR/design doc
- [ ] SMTP, secrets, env var management documented; log PII policy documented
- [ ] Per-recipient retry and "max 3 retries then escalate" recording agreed
- [ ] First Phase 2 dev story has Definition of Ready (acceptance, test approach, deps)
- [ ] Sprint Prioritizer output: ordered backlog and visible blockers
- [ ] Reality Checker Phase 1 feasibility review complete (final launch approval still required)
- [ ] Open questions have owner or deferred phase
```
