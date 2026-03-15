# 🔍 Phase 0 Playbook — Intelligence & Discovery

> **Duration**: 3-7 days | **Agents**: 6 | **Gate Keeper**: Executive Summary Generator

---

## Objective

Validate the opportunity before committing resources. No building until the problem, market, and regulatory landscape are understood.

## Pre-Conditions

- [ ] Project brief or initial concept exists
- [ ] Stakeholder sponsor identified
- [ ] Budget for discovery phase approved

## Agent Activation Sequence

### Wave 1: Parallel Launch (Day 1)

#### 🔍 Trend Researcher — Market Intelligence Lead
```
Activate Trend Researcher for market intelligence on [PROJECT DOMAIN].

Deliverables required:
1. Competitive landscape analysis (direct + indirect competitors)
2. Market sizing: TAM, SAM, SOM with methodology
3. Trend lifecycle mapping: where is this market in the adoption curve?
4. 3-6 month trend forecast with confidence intervals
5. Investment and funding trends in the space

Sources: Minimum 15 unique, verified sources
Format: Strategic Report with executive summary
Timeline: 3 days
```

#### 💬 Feedback Synthesizer — User Needs Analysis
```
Activate Feedback Synthesizer for user needs analysis on [PROJECT DOMAIN].

Deliverables required:
1. Multi-channel feedback collection plan (surveys, interviews, reviews, social)
2. Sentiment analysis across existing user touchpoints
3. Pain point identification and prioritization (RICE scored)
4. Feature request analysis with business value estimation
5. Churn risk indicators from feedback patterns

Format: Synthesized Feedback Report with priority matrix
Timeline: 3 days
```

#### 🔍 UX Researcher — User Behavior Analysis
```
Activate UX Researcher for user behavior analysis on [PROJECT DOMAIN].

Deliverables required:
1. User interview plan (5-10 target users)
2. Persona development (3-5 primary personas)
3. Journey mapping for primary user flows
4. Usability heuristic evaluation of competitor products
5. Behavioral insights with statistical validation

Format: Research Findings Report with personas and journey maps
Timeline: 5 days
```

### Wave 2: Parallel Launch (Day 1, independent of Wave 1)

#### 📊 Analytics Reporter — Data Landscape Assessment
```
Activate Analytics Reporter for data landscape assessment on [PROJECT DOMAIN].

Deliverables required:
1. Existing data source audit (what data is available?)
2. Signal identification (what can we measure?)
3. Baseline metrics establishment
4. Data quality assessment with completeness scoring
5. Analytics infrastructure recommendations

Format: Data Audit Report with signal map
Timeline: 2 days
```

#### ⚖️ Legal Compliance Checker — Regulatory Scan
```
Activate Legal Compliance Checker for regulatory scan on [PROJECT DOMAIN].

Deliverables required:
1. Applicable regulatory frameworks (GDPR, CCPA, HIPAA, etc.)
2. Data handling requirements and constraints
3. Jurisdiction mapping for target markets
4. Compliance risk assessment with severity ratings
5. Blocking vs. manageable compliance issues

Format: Compliance Requirements Matrix
Timeline: 3 days
```

#### 🛠️ Tool Evaluator — Technology Landscape
```
Activate Tool Evaluator for technology landscape assessment on [PROJECT DOMAIN].

Deliverables required:
1. Technology stack assessment for the problem domain
2. Build vs. buy analysis for key components
3. Integration feasibility with existing systems
4. Open source vs. commercial evaluation
5. Technology risk assessment

Format: Tech Stack Assessment with recommendation matrix
Timeline: 2 days
```

## Convergence Point (Day 5-7)

All six agents deliver their reports. The Executive Summary Generator synthesizes:

```
Activate Executive Summary Generator to synthesize Phase 0 findings.

Input documents:
1. Trend Researcher → Market Analysis Report
2. Feedback Synthesizer → Synthesized Feedback Report
3. UX Researcher → Research Findings Report
4. Analytics Reporter → Data Audit Report
5. Legal Compliance Checker → Compliance Requirements Matrix
6. Tool Evaluator → Tech Stack Assessment

Output: Executive Summary (≤500 words, SCQA format)
Decision required: GO / NO-GO / PIVOT
Include: Quantified market opportunity, validated user needs, regulatory path, technology feasibility
```

## Quality Gate Checklist

| # | Criterion | Evidence Source | Status |
|---|-----------|----------------|--------|
| 1 | Market opportunity validated with TAM > minimum viable threshold | Trend Researcher report | ☐ |
| 2 | ≥3 validated user pain points with supporting data | Feedback Synthesizer + UX Researcher | ☐ |
| 3 | No blocking compliance issues identified | Legal Compliance Checker matrix | ☐ |
| 4 | Key metrics and data sources identified | Analytics Reporter audit | ☐ |
| 5 | Technology stack feasible and assessed | Tool Evaluator assessment | ☐ |
| 6 | Executive summary delivered with GO/NO-GO recommendation | Executive Summary Generator | ☐ |

## Gate Decision

- **GO**: Proceed to Phase 1 — Strategy & Architecture
- **NO-GO**: Archive findings, document learnings, redirect resources
- **PIVOT**: Modify scope/direction based on findings, re-run targeted discovery

## Handoff to Phase 1

```markdown
## Phase 0 → Phase 1 Handoff Package

### Documents to carry forward:
1. Market Analysis Report (Trend Researcher)
2. Synthesized Feedback Report (Feedback Synthesizer)
3. User Personas and Journey Maps (UX Researcher)
4. Data Audit Report (Analytics Reporter)
5. Compliance Requirements Matrix (Legal Compliance Checker)
6. Tech Stack Assessment (Tool Evaluator)
7. Executive Summary with GO decision (Executive Summary Generator)

### Key constraints identified:
- [Regulatory constraints from Legal Compliance Checker]
- [Technical constraints from Tool Evaluator]
- [Market timing constraints from Trend Researcher]

### Priority user needs (for Sprint Prioritizer):
1. [Pain point 1 — from Feedback Synthesizer]
2. [Pain point 2 — from UX Researcher]
3. [Pain point 3 — from Feedback Synthesizer]
```

---

*Phase 0 is complete when the Executive Summary Generator delivers a GO decision with supporting evidence from all six discovery agents.*
