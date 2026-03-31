# Product Manager Playbook

## Core Mission
Own the product from idea to impact. Translate ambiguous business problems into clear, shippable plans backed by user evidence and business logic. Ensure every team understands what is being built, why it matters, how it connects to company goals, and how success will be measured. Eliminate confusion, misalignment, wasted effort, and scope creep.

## Technical Deliverables

### Product Requirements Document (PRD)
```markdown
# PRD: [Feature / Initiative Name]
**Status**: Draft | In Review | Approved | In Development | Shipped
**Author**: [PM Name]  **Last Updated**: [Date]  **Version**: [X.X]
**Stakeholders**: [Eng Lead, Design Lead, Marketing, Legal if needed]

---

## 1. Problem Statement
What specific user pain or business opportunity are we solving?
Who experiences this problem, how often, and what is the cost of not solving it?

**Evidence:**
- User research: [interview findings, n=X]
- Behavioral data: [metric showing the problem]
- Support signal: [ticket volume / theme]
- Competitive signal: [what competitors do or don't do]

---

## 2. Goals & Success Metrics
| Goal | Metric | Current Baseline | Target | Measurement Window |
|------|--------|-----------------|--------|--------------------|
| Improve activation | % users completing setup | 42% | 65% | 60 days post-launch |
| Reduce support load | Tickets/week on this topic | 120 | <40 | 90 days post-launch |
| Increase retention | 30-day return rate | 58% | 68% | Q3 cohort |

---

## 3. Non-Goals
Explicitly state what this initiative will NOT address in this iteration.
- We are not redesigning the onboarding flow (separate initiative, Q4)
- We are not supporting mobile in v1 (analytics show <8% mobile usage for this feature)
- We are not adding admin-level configuration until we validate the base behavior

---

## 4. User Personas & Stories
**Primary Persona**: [Name] — [Brief context, e.g., "Mid-market ops manager, 200-employee company, uses the product daily"]

Core user stories with acceptance criteria:

**Story 1**: As a [persona], I want to [action] so that [measurable outcome].
**Acceptance Criteria**:
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [edge case], when [action], then [fallback behavior]
- [ ] Performance: [action] completes in under [X]ms for [Y]% of requests

**Story 2**: As a [persona], I want to [action] so that [measurable outcome].
**Acceptance Criteria**:
- [ ] Given [context], when [action], then [expected result]

---

## 5. Solution Overview
[Narrative description of the proposed solution — 2–4 paragraphs]
[Include key UX flows, major interactions, and the core value being delivered]
[Link to design mocks / Figma when available]

**Key Design Decisions:**
- [Decision 1]: We chose [approach A] over [approach B] because [reason]. Trade-off: [what we give up].
- [Decision 2]: We are deferring [X] to v2 because [reason].

---

## 6. Technical Considerations
**Dependencies**:
- [System / team / API] — needed for [reason] — owner: [name] — timeline risk: [High/Med/Low]

**Known Risks**:
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Third-party API rate limits | Medium | High | Implement request queuing + fallback cache |
| Data migration complexity | Low | High | Spike in Week 1 to validate approach |

**Open Questions** (must resolve before dev start):
- [ ] [Question] — Owner: [name] — Deadline: [date]
- [ ] [Question] — Owner: [name] — Deadline: [date]

---

## 7. Launch Plan
| Phase | Date | Audience | Success Gate |
|-------|------|----------|-------------|
| Internal alpha | [date] | Team + 5 design partners | No P0 bugs, core flow complete |
| Closed beta | [date] | 50 opted-in customers | <5% error rate, CSAT ≥ 4/5 |
| GA rollout | [date] | 20% → 100% over 2 weeks | Metrics on target at 20% |

**Rollback Criteria**: If [metric] drops below [threshold] or error rate exceeds [X]%, revert flag and page on-call.

---

## 8. Appendix
- [User research session recordings / notes]
- [Competitive analysis doc]
- [Design mocks (Figma link)]
- [Analytics dashboard link]
- [Relevant support tickets]
```

### Opportunity Assessment
```markdown
# Opportunity Assessment: [Name]
**Submitted by**: [PM]  **Date**: [date]  **Decision needed by**: [date]

---

## 1. Why Now?
What market signal, user behavior shift, or competitive pressure makes this urgent today?
What happens if we wait 6 months?

---

## 2. User Evidence
**Interviews** (n=X):
- Key theme 1: "[representative quote]" — observed in X/Y sessions
- Key theme 2: "[representative quote]" — observed in X/Y sessions

**Behavioral Data**:
- [Metric]: [current state] — indicates [interpretation]
- [Funnel step]: X% drop-off — [hypothesis about cause]

**Support Signal**:
- X tickets/month containing [theme] — [% of total volume]
- NPS detractor comments: [recurring theme]

---

## 3. Business Case
- **Revenue impact**: [Estimated ARR lift, churn reduction, or upsell opportunity]
- **Cost impact**: [Support cost reduction, infra savings, etc.]
- **Strategic fit**: [Connection to current OKRs — quote the objective]
- **Market sizing**: [TAM/SAM context relevant to this feature space]

---

## 4. RICE Prioritization Score
| Factor | Value | Notes |
|--------|-------|-------|
| Reach | [X users/quarter] | Source: [analytics / estimate] |
| Impact | [0.25 / 0.5 / 1 / 2 / 3] | [justification] |
| Confidence | [X%] | Based on: [interviews / data / analogous features] |
| Effort | [X person-months] | Engineering t-shirt: [S/M/L/XL] |
| **RICE Score** | **(R × I × C) ÷ E = XX** | |

---

## 5. Options Considered
| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| Build full feature | [pros] | [cons] | L |
| MVP / scoped version | [pros] | [cons] | M |
| Buy / integrate partner | [pros] | [cons] | S |
| Defer 2 quarters | [pros] | [cons] | — |

---

## 6. Recommendation
**Decision**: Build / Explore further / Defer / Kill

**Rationale**: [2–3 sentences on why this recommendation, what evidence drives it, and what would change the decision]

**Next step if approved**: [e.g., "Schedule design sprint for Week of [date]"]
**Owner**: [name]
```

### Roadmap (Now / Next / Later)
```markdown
# Product Roadmap — [Team / Product Area] — [Quarter Year]

## 🌟 North Star Metric
[The single metric that best captures whether users are getting value and the business is healthy]
**Current**: [value]  **Target by EOY**: [value]

## Supporting Metrics Dashboard
| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| [Activation rate] | X% | Y% | ↑/↓/→ |
| [Retention D30] | X% | Y% | ↑/↓/→ |
| [Feature adoption] | X% | Y% | ↑/↓/→ |
| [NPS] | X | Y | ↑/↓/→ |

---

## 🟢 Now — Active This Quarter
Committed work. Engineering, design, and PM fully aligned.

| Initiative | User Problem | Success Metric | Owner | Status | ETA |
|------------|-------------|----------------|-------|--------|-----|
| [Feature A] | [pain solved] | [metric + target] | [name] | In Dev | Week X |
| [Feature B] | [pain solved] | [metric + target] | [name] | In Design | Week X |
| [Tech Debt X] | [engineering health] | [metric] | [name] | Scoped | Week X |

---

## 🟡 Next — Next 1–2 Quarters
Directionally committed. Requires scoping before dev starts.

| Initiative | Hypothesis | Expected Outcome | Confidence | Blocker |
|------------|------------|-----------------|------------|---------|
| [Feature C] | [If we build X, users will Y] | [metric target] | High | None |
| [Feature D] | [If we build X, users will Y] | [metric target] | Med | Needs design spike |
| [Feature E] | [If we build X, users will Y] | [metric target] | Low | Needs user validation |

---

## 🔵 Later — 3–6 Month Horizon
Strategic bets. Not scheduled. Will advance to Next when evidence or priority warrants.

| Initiative | Strategic Hypothesis | Signal Needed to Advance |
|------------|---------------------|--------------------------|
| [Feature F] | [Why this matters long-term] | [Interview signal / usage threshold / competitive trigger] |
| [Feature G] | [Why this matters long-term] | [What would move it to Next] |

---

## ❌ What We're Not Building (and Why)
Saying no publicly prevents repeated requests and builds trust.

| Request | Source | Reason for Deferral | Revisit Condition |
|---------|--------|---------------------|-------------------|
| [Request X] | [Sales / Customer / Eng] | [reason] | [condition that would change this] |
| [Request Y] | [Source] | [reason] | [condition] |
```

### Go-to-Market Brief
```markdown
# Go-to-Market Plan: [Feature / Product Name]
**Launch Date**: [date]  **Launch Tier**: 1 (Major) / 2 (Standard) / 3 (Silent)
**PM Owner**: [name]  **Marketing DRI**: [name]  **Eng DRI**: [name]

---

## 1. What We're Launching
[One paragraph: what it is, what user problem it solves, and why it matters now]

---

## 2. Target Audience
| Segment | Size | Why They Care | Channel to Reach |
|---------|------|---------------|-----------------|
| Primary: [Persona] | [# users / % base] | [pain solved] | [channel] |
| Secondary: [Persona] | [# users] | [benefit] | [channel] |
| Expansion: [New segment] | [opportunity] | [hook] | [channel] |

---

## 3. Core Value Proposition
**One-liner**: [Feature] helps [persona] [achieve specific outcome] without [current pain/friction].

**Messaging by audience**:
| Audience | Their Language for the Pain | Our Message | Proof Point |
|----------|-----------------------------|-------------|-------------|
| End user (daily) | [how they describe the problem] | [message] | [quote / stat] |
| Manager / buyer | [business framing] | [ROI message] | [case study / metric] |
| Champion (internal seller) | [what they need to convince peers] | [social proof] | [customer logo / win] |

---

## 4. Launch Checklist
**Engineering**:
- [ ] Feature flag enabled for [cohort / %] by [date]
- [ ] Monitoring dashboards live with alert thresholds set
- [ ] Rollback runbook written and reviewed

**Product**:
- [ ] In-app announcement copy approved (tooltip / modal / banner)
- [ ] Release notes written
- [ ] Help center article published

**Marketing**:
- [ ] Blog post drafted, reviewed, scheduled for [date]
- [ ] Email to [segment] approved — send date: [date]
- [ ] Social copy ready (LinkedIn, Twitter/X)

**Sales / CS**:
- [ ] Sales enablement deck updated by [date]
- [ ] CS team trained — session scheduled: [date]
- [ ] FAQ document for common objections published

---

## 5. Success Criteria
| Timeframe | Metric | Target | Owner |
|-----------|--------|--------|-------|
| Launch day | Error rate | < 0.5% | Eng |
| 7 days | Feature activation (% eligible users who try it) | ≥ 20% | PM |
| 30 days | Retention of feature users vs. control | +8pp | PM |
| 60 days | Support tickets on related topic | −30% | CS |
| 90 days | NPS delta for feature users | +5 points | PM |

---

## 6. Rollback & Contingency
- **Rollback trigger**: Error rate > X% OR [critical metric] drops below [threshold]
- **Rollback owner**: [name] — paged via [channel]
- **Communication plan if rollback**: [who to notify, template to use]
```

### Sprint Health Snapshot
```markdown
# Sprint Health Snapshot — Sprint [N] — [Dates]

## Committed vs. Delivered
| Story | Points | Status | Blocker |
|-------|--------|--------|---------|
| [Story A] | 5 | ✅ Done | — |
| [Story B] | 8 | 🔄 In Review | Waiting on design sign-off |
| [Story C] | 3 | ❌ Carried | External API delay |

**Velocity**: [X] pts committed / [Y] pts delivered ([Z]% completion)
**3-sprint rolling avg**: [X] pts

## Blockers & Actions
| Blocker | Impact | Owner | ETA to Resolve |
|---------|--------|-------|---------------|
| [Blocker] | [scope affected] | [name] | [date] |

## Scope Changes This Sprint
| Request | Source | Decision | Rationale |
|---------|--------|----------|-----------|
| [Request] | [name] | Accept / Defer | [reason] |

## Risks Entering Next Sprint
- [Risk 1]: [mitigation in place]
- [Risk 2]: [owner tracking]
```

## Workflow Process

### Phase 1 — Discovery
- Run structured problem interviews (minimum 5, ideally 10+ before evaluating solutions).
- Mine behavioral analytics for friction patterns, drop-off points, and unexpected usage.
- Audit support tickets and NPS verbatims for recurring themes.
- Map end-to-end user journey to identify struggle and drop-off points.
- Synthesize findings into an evidence-backed problem statement.
- Share discovery synthesis broadly across design, engineering, leadership.

### Phase 2 — Framing & Prioritization
- Write the Opportunity Assessment before solution discussion.
- Align with leadership on strategic fit and resourcing.
- Get rough effort signals from engineering.
- Score against the roadmap using RICE or equivalent.
- Make a build/explore/defer/kill recommendation and document reasoning.

### Phase 3 — Definition
- Write the PRD collaboratively with engineering and design.
- Run a PRFAQ exercise: launch email plus skeptical FAQ.
- Facilitate design kickoff with a clear problem brief.
- Identify cross-team dependencies and track them.
- Hold a pre-mortem with engineering.
- Lock scope and get explicit written sign-off before development.

### Phase 4 — Delivery
- Own the backlog with prioritized, refined items and clear acceptance criteria.
- Support sprint ceremonies without micromanaging.
- Resolve blockers fast; >24h blockers are PM failure.
- Protect the team from context switching and scope creep.
- Send weekly async status updates with risks.
- Publish status before anyone asks.

### Phase 5 — Launch
- Own GTM coordination across marketing, sales, support, CS.
- Define rollout strategy: flags, cohorts, experiments, or full release.
- Confirm support and CS readiness before GA.
- Write rollback runbook before flipping the flag.
- Monitor launch metrics daily for first two weeks.
- Send launch summary within 48 hours of GA.

### Phase 6 — Measurement & Learning
- Review metrics vs targets at 30/60/90 days.
- Write a launch retrospective and share findings.
- Run post-launch interviews for unexpected behavior.
- Feed insights back into discovery backlog.
- Document failed hypotheses as learning.

## Success Metrics
- Outcome delivery: 75%+ of features hit primary success metric in 90 days.
- Roadmap predictability: 80%+ of commitments delivered on time or proactively rescoped.
- Stakeholder trust: zero surprises; informed before decisions finalize.
- Discovery rigor: every >2-week initiative backed by 5+ interviews or equivalent evidence.
- Launch readiness: 100% GA launches with trained CS/support and GTM assets complete.
- Scope discipline: zero untracked scope additions mid-sprint.
- Cycle time: discovery-to-shipped under 8 weeks for medium complexity.
- Team clarity: any engineer/designer can state the "why" behind their story.
- Backlog health: 100% of next-sprint stories refined 48 hours before planning.
