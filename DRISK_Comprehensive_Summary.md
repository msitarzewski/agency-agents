 DRISK – Digital Risk Intelligence for Security
## Complete Software Platform Summary

---

## EXECUTIVE SUMMARY

DRISK is an enterprise-grade digital risk intelligence platform designed to help organisations assess, understand, and improve physical security risk across multiple locations. It combines structured site assessments, intelligent risk scoring, action tracking, operational recommendations, and executive reporting in one unified system.

Rather than relying on static consultant reports, manual spreadsheets, or inconsistent judgement, DRISK provides a clear, repeatable, evidence-led approach to identifying vulnerabilities, prioritising investment, and proving security improvement over time.

**Created by:** Delta Force Group — a security operator with direct frontline operational credibility across guarding, mobile patrols, keyholding, alarm response, compliance, and contract performance.

---

## POSITIONING STATEMENT

*"DRISK is a protective-security intelligence and optimisation platform that helps organisations assess, evidence, prioritise and improve physical-security risk across their estates, while linking risk decisions directly to operational delivery, compliance readiness and cost optimisation."*

---

## CORE MARKET PROMISE

> **"Safer environments, smarter spend, provable compliance, and live operational control."**

This is stronger than "digital risk assessments" because Delta Force can connect risk intelligence to actual service delivery — something software-only providers cannot.

---

## WHAT DRISK IS (AND IS NOT)

### DRISK IS:
A system that connects:
- Site risk
- Control effectiveness
- Response capability
- Compliance duties
- Operational actions
- Executive decision-making

### DRISK IS NOT:
- Just a digital checklist
- Just a PDF report generator
- Just a traffic-light dashboard
- Just a guard deployment app

---

## THE PROBLEM DRISK SOLVES

Physical security risk management is fragmented and outdated:

- **Inconsistent assessments** – Sites are difficult to compare consistently across a portfolio
- **Recurring weaknesses** – Hard to identify patterns in failure across multiple locations
- **Untracked actions** – Improvements are not always monitored or verified
- **Misaligned spend** – Resources may be insufficient in high-risk areas or excessive in lower-risk locations
- **Weak governance** – Security decisions lack clear evidence or documented justification
- **Poor visibility** – Decision-makers struggle to articulate why security spend is allocated in certain areas
- **Subjective decision-making** – Reliance on opinion rather than data

**Result:** Organisations often over-invest in low-risk areas while under-protecting critical sites, and lack strong evidence for their security decisions.

---

## THE DRISK SOLUTION

DRISK creates a single, standardised operating model for protective security risk management:

1. **Captures site conditions** through structured, guided assessments
2. **Applies consistent scoring methodology** to convert findings into comparable risk metrics
3. **Shows control effectiveness and residual risk** at a granular level
4. **Tracks corrective actions** and monitors progress toward completion
5. **Translates findings into practical recommendations** that can be operationalised
6. **Produces executive-ready reports** that evidence security decisions
7. **Enables trend analysis** and comparison over time

---

## TARGET MARKET & WHO DRISK IS FOR

DRISK is built for organisations that manage multiple locations, sensitive sites, public-facing premises, or environments where security decisions must be justified operationally and commercially.

**Priority Sectors:**
- NHS and healthcare providers
- Universities and colleges
- Local authorities
- Housing associations and supported accommodation
- Logistics and distribution
- Multi-site commercial estates
- Vacant property portfolios
- Event and public-access venues

These sectors fit because they need some mix of public safety, duty-of-care evidence, operational response, and cost control.

---

## CORE VALUE PROPOSITION — 5 STRATEGIC QUESTIONS

DRISK helps clients answer five critical questions better than any competitor:

1. **What are my highest-risk sites and assets?** – Identify genuine exposure across your estate
2. **Which controls are weak, missing, excessive, or failing?** – Understand whether protective measures are effective
3. **What is my cheapest safe operating model?** – Find cost-efficient protection
4. **What do I need to do to meet emerging UK security expectations and duties?** – Stay ahead of regulation (including Martyn's Law)
5. **How do I prove improvement over time?** – Make better investment decisions with hard evidence

---

## REGULATORY CONTEXT — MARTYN'S LAW

**The Terrorism (Protection of Premises) Act 2025** received Royal Assent on 3 April 2025, with an implementation period of at least 24 months. Many organisations are now in a preparation phase.

DRISK is positioned as one of the easiest ways for clients to prepare for UK protective-security expectations, including Martyn's Law planning where in scope.

---

## UK POLICE CRIME API INTEGRATION

DRISK integrates with the **UK Police open data API** (data.police.uk) to automatically populate real crime intelligence into the DRISK Intelligence module and External Threat scoring domain — eliminating manual research and making threat scores evidence-backed and current.

### What It Provides

The API is **free, public, and requires no authentication**. It covers England, Wales, and Northern Ireland (with some limitations). It returns:

- **Street-level crime incidents** by location (lat/lng) or polygon area
- **Crime categories** including: anti-social behaviour, burglary, robbery, violent crime, vehicle crime, criminal damage and arson, drugs, public order, theft, weapons possession
- **Outcome data** – how crimes were resolved (charged, cautioned, local resolution, no further action, etc.)
- **Stop and search data** by area
- **Data freshness indicator** – timestamp of last data update

### How It Feeds Into DRISK

| API Data | DRISK Use |
|----------|-----------|
| Crime volume near site (lat/lng radius) | Auto-populates External Threat domain score |
| ASB incidents | Contributes to Threat score (Layer A) |
| Violent crime rate | Elevates inherent risk rating |
| Burglary / vehicle crime | Feeds physical security risk context |
| Crime outcome rates | Indicates policing effectiveness as response factor |
| Monthly trend data | Powers the Live Residual-Risk Engine (Innovation 1) |

### Key API Endpoints Used

- `GET /api/crimes-street/all-crime?lat={lat}&lng={lng}&date={YYYY-MM}` — all crimes within 1 mile of site
- `GET /api/crimes-street/violent-crime?lat={lat}&lng={lng}` — violent crime specifically
- `GET /api/crime-categories?date={YYYY-MM}` — available category codes
- `GET /api/crimes-street-outcomes?lat={lat}&lng={lng}&date={YYYY-MM}` — crime outcomes
- `GET /api/stops-street?lat={lat}&lng={lng}&date={YYYY-MM}` — stop and search data

### Rate Limits

- Average: **15 requests per second**
- Burst: **up to 30 requests per second**
- No API key required

### Value to DRISK

- Threat scores become **data-driven**, not assessor opinion
- External threat context is **automatically refreshed** monthly
- Sites in high-crime areas are **flagged automatically** before an assessor visits
- Crime trend changes can **trigger live residual-risk updates** (Innovation 1)
- Clients can see exactly **why** a site has a high threat score — backed by police data

---

## PRODUCT ARCHITECTURE — 7 CONNECTED MODULES

DRISK is built as **seven connected modules**:

### Module 1: DRISK Profile
Creates the protection baseline for each client, estate, site, and asset.

Captures:
- Client risk appetite
- Critical assets
- Vulnerable persons / high-sensitivity populations
- Site use and operating hours
- Public accessibility
- Critical dependencies
- Board / accountable owner
- Legal and policy requirements
- Required response standards

### Module 2: DRISK Assess
Mobile and web-based structured assessments used by:
- Consultants
- Supervisors
- Contract managers
- Client representatives
- Trained site assessors

Assessment outputs must be standardised and evidence-backed, not free-form opinion.

### Module 3: DRISK Intelligence
External and internal context layer — automatically enriched by the **UK Police Crime API** (data.police.uk).

Inputs include:
- **Crime context** – auto-pulled from UK Police API by site lat/lng (street-level crimes, categories, volumes)
- **Crime outcome data** – resolution rates indicating local policing effectiveness
- **Stop and search data** – disorder and enforcement activity near site
- Local incident patterns
- Deprivation / environmental context
- Protest / disorder sensitivity
- Critical-neighbour proximity
- Local vulnerability indicators
- Historical site incidents
- Staffing and patrol performance signals

### Module 4: DRISK Score
The automated scoring engine.

Calculates:
- Inherent risk
- Control effectiveness
- Response strength
- Residual risk
- Compliance readiness
- Confidence score
- Optimisation potential

### Module 5: DRISK Act
Action-management and remediation.

Creates:
- Tasks
- Deadlines
- Owners
- Evidence requirements
- Verification steps
- Residual-risk updates after closure

### Module 6: DRISK Command
Operational integration layer — **where Delta Force beats software-only providers**.

Translates findings into:
- Assignment instructions
- Patrol requirements
- Supervisor checks
- Escalation matrices
- Officer briefings
- Site improvement plans

### Module 7: DRISK Board
Executive reporting and funding justification.

Outputs:
- Estate heatmaps
- Capital-vs-operational investment choices
- Compliance-readiness status
- Board summaries
- Insurance / audit summaries
- Tender-grade innovation reporting

---

## LAYERED RISK MODEL — 6 LAYERS

DRISK uses a layered model rather than a single raw score:

### Layer A: Inherent Risk
Measures the exposure **before** considering current controls.
- **Formula: Threat × Vulnerability × Impact**
- Each factor scored 1–5
- Example: Threat (4) × Vulnerability (3) × Impact (4) = 48

### Layer B: Control Effectiveness
Measures how well current measures perform across deterrence, detection, delay, and response.

Control Multiplier examples:
| Control Strength | Multiplier |
|-----------------|------------|
| Strong | 0.6 |
| Moderate | 0.8 |
| Weak | 1.0 |

### Layer C: Response Capability
Measures whether the site can react effectively when controls are challenged.

Includes:
- Escalation speed
- Guard capability
- Response SLA
- Communications resilience
- Command clarity
- Fallback arrangements

Response Multiplier examples:
| Response Capability | Multiplier |
|---------------------|------------|
| Strong | 0.7 |
| Moderate | 0.85 |
| Weak | 1.0 |

### Layer D: Residual Risk
Measures exposure **after** current controls and response arrangements are taken into account.
- **Formula: Inherent Risk × Control Multiplier × Response Multiplier**
- Example: 48 × 0.8 × 0.85 = Residual Risk of 32.64

### Layer E: Compliance Readiness
Measures whether the site can evidence the right procedures, responsibilities, actions, and proof.
- Policy alignment
- Training records
- Action closure quality
- Audit-ready documentation

### Layer F: Optimisation Score
Measures whether current spend is underweight, efficient, or excessive against baseline needs.

Output categories:
- **Under-protected** – Insufficient controls relative to risk
- **Correctly protected** – Controls match risk level
- **Over-protected** – Excessive controls relative to risk

---

## RISK BANDS & CLASSIFICATION

| Score | Risk Band | Action Required |
|-------|-----------|-----------------|
| 0–15 | **Low** | Standard controls adequate |
| 16–30 | **Moderate** | Review controls regularly |
| 31–50 | **High** | Improvements recommended |
| 51–75 | **Very High** | Urgent action required |
| 76+ | **Critical** | Immediate intervention needed |

---

## CONFIDENCE SCORE

Measures how reliable the assessment result is.

| Confidence Level | Score |
|------------------|-------|
| High | 90–100% |
| Medium | 70–89% |
| Low | Below 70% |

Factors that reduce confidence:
- Unanswered questions
- Unknown responses
- Missing evidence
- Assessor uncertainty

---

## 10 SCORING DOMAINS

DRISK scores every site across **10 domains** (not just 8):

### Domain 1: Site Context
- Site type and function
- Hours of operation
- Occupancy profile
- Isolated or urban setting
- Public access level
- Vulnerable occupants
- Critical service dependency
- Previous incident history
- Surrounding area characteristics

### Domain 2: Asset Criticality
- People
- Data rooms / comms rooms
- Medicines / dangerous goods
- Cash / high-value stock
- Keys / access credentials
- Essential infrastructure
- Reputation-sensitive spaces

### Domain 3: External Threat Context
- Local crime exposure
- Violent incident patterns
- Anti-social behaviour levels
- Protest / disorder potential
- Terrorism relevance (where appropriate)
- Hostile vehicle approach opportunity
- Night-time activity patterns
- Ease of hostile approach
- Nearby transport links and access routes

### Domain 4: Physical Protection
- Perimeter fencing and walls
- Access points and gates
- Locks and doors
- Windows and glazing
- Shutters and barriers
- Bollards and hostile vehicle mitigation
- External and internal lighting
- CCTV coverage
- Intruder alarm systems
- Plant room, roof, rear access, and service-entry protection

### Domain 5: Access Governance
- Visitor management process
- Credential management
- Joiner / mover / leaver process
- Contractor access control
- Key management
- Card / fob control
- Access review practices
- Restricted-zone governance

### Domain 6: Human and Procedural Controls
- Guarding model
- Patrol frequency and coverage
- Opening and closing procedures
- Searching / screening (where relevant)
- Incident reporting quality
- Escalation processes
- Handover discipline
- Lone worker protection
- Officer briefing and awareness
- Supervisor assurance activity

### Domain 7: Response Capability
- First response arrangements
- Mobile response support
- Supervisor attendance
- Emergency communication
- Command and escalation clarity
- Communications resilience
- Control room support
- Fallback arrangements
- Business continuity linkages

### Domain 8: Insider and Role-Based Exposure
Aligned with NPSA role-based guidance:
- Privileged access concentration
- Lone access to critical spaces
- Contractor privileges
- Unmanaged master keys / cards
- Vetting alignment
- Weak segregation of duties
- Access review failures
- Unsupervised contractor movement

### Domain 9: Resilience and Recovery
Aligned with ISO 22301:
- Continuity dependence
- Backup arrangements
- Alternative operating arrangements
- Critical supplier reliance
- Outage tolerance
- Restoration readiness

### Domain 10: Compliance and Assurance
- Evidence completeness
- Policy alignment
- Training records
- Drill / exercise history
- Action closure quality
- Review frequency
- Accountable owner visibility
- Documented procedures
- Assurance audits

---

## 4-TIER ASSESSMENT STRUCTURE

DRISK supports four tiers of assessment, enabling scale without losing depth:

### Tier 1: Rapid Triage
- **Duration:** 10–15 minutes
- **Used for:** Portfolio screening, tender mobilisation, site onboarding

### Tier 2: Standard Assessment
- **Duration:** 45–90 minutes
- **Used for:** Mainstream multi-site assessment for normal clients

### Tier 3: Enhanced Protective-Security Assessment
- **Depth:** Full review
- **Used for:** Critical, public-facing, sensitive, or regulated sites requiring deeper review

### Tier 4: Scenario / Event-Specific Assessment
- **Used for:**
  - Public disorder events
  - Protests
  - Heightened threat periods
  - VIP visits
  - Vacant-period exposure
  - Event surges
  - Major incident preparedness

---

## STRUCTURED ASSESSMENT QUESTION BANK — 50 CORE QUESTIONS

DRISK includes approximately **50 core questions** across the 10 domains. Each question includes:

- **Fixed wording** (ensures consistency across assessors)
- **Predefined answer options** (scored 1, 3, 5)
- **Scoring logic** (automated calculation)
- **Weight** (criticality indicator: 1–4)
- **Evidence requirement** (what to capture)
- **Optional assessor comment field**
- **Not applicable option**

**Question Weight Scale:**
- Weight 1: Low impact issues
- Weight 2: Operational controls
- Weight 3: Critical security measures
- Weight 4: Life safety or high-risk vulnerabilities

**Formula: Weighted Score = Base Score × Question Weight**

**Example Questions by Domain:**

**Domain 1 – Site Context:**
- Q1: Primary function of site? (Low sensitivity / Mixed / Sensitive)
- Q2: Is site publicly accessible? (Fully restricted / Partially public / Fully public-facing)
- Q3: Does site accommodate vulnerable persons? (No / Limited / Regular/significant)
- Q4: Are critical services delivered from this site? (No / Moderate / Critical)

**Domain 3 – External Threat:**
- Q5: Located in high-crime or disorder area? (Low / Medium / High risk)
- Q6: Is trespass or ASB evident? (Not evident / Occasional / Frequent)
- Q7: Is site isolated during low occupancy? (No / Partially / Highly isolated)

**Domain 4 – Physical Security:**
- Q8: Is perimeter clearly defined and secured? (Yes / Partially / No)
- Q9: Are entry points physically secure? (Fully / Partially / Insecure)
- Q10: Is CCTV installed at key areas? (Full / Partial / No coverage)
- Q11: Is external lighting sufficient? (Adequate / Moderate / Poor)
- Q17: Is external lighting sufficient to support deterrence and visibility? (Sufficient / Partly / Insufficient)

**Domain 5 – Access Control:**
- Q12: Is there a visitor management process? (Yes / Partially / No process)
- Q13: Are access credentials controlled and reviewed? (Fully / Some / No control)
- Q14: Are restricted areas clearly defined? (Yes / Partially / No)
- Q26: Are access cards, fobs, keys, or credentials issued and withdrawn under controlled procedures? (Controlled / Partly / Uncontrolled)

**Domain 6 – Human & Procedural:**
- Q15: Are security patrols structured and recorded? (Yes / Partially / No)
- Q16: Are opening and closing procedures documented? (Yes / Partially / No)
- Q17: Are incidents recorded and escalated properly? (Yes / Sometimes / No)

**Domain 7 – Response & Resilience:**
- Q18: Is there a clear incident response plan? (Clear/documented / Basic / No plan)
- Q19: Are response times adequate for site risk? (Adequate / Moderate / Inadequate)
- Q20: Are communication systems reliable? (Reliable / Sometimes / Unreliable)
- Q38: Are response times appropriate for the site risk level? (Appropriate / Partly / Inadequate)

**Domain 8 – Insider Risk:**
- Q21: Are privileged access rights restricted? (Yes / Partially / No)
- Q22: Are master keys and critical credentials controlled? (Controlled / Partially / Uncontrolled)

**Domain 10 – Compliance & Assurance:**
- Q23: Is there a current site risk assessment? (Current / Outdated / None)
- Q24: Are audit actions tracked to completion? (Yes / Partially / No)
- Q25: Is there evidence of ongoing security review? (Yes / Limited / No)

---

## 6 REQUIRED INNOVATIONS

To lead the market, DRISK includes innovations that go beyond standard risk software:

### Innovation 1: Live Residual-Risk Engine
Risk changes when operational reality changes — not just after annual assessments.

Triggers include:
- CCTV fault unresolved for 7+ days
- Patrol failures rising
- Officer no-shows occurring
- Access-control faults staying open
- Recent incident cluster appearing
- Threat posture changing

This creates a **living risk picture** instead of a static annual assessment.

### Innovation 2: Cost-to-Control Optimiser
For each recommendation, DRISK ranks options by:
- Risk reduction
- Implementation speed
- Capital spend
- Recurring spend
- Manpower substitution potential
- Compliance benefit

### Innovation 3: Martyn's Law Readiness Workflow
One of the strongest market opportunities in the UK. DRISK includes a dedicated workflow for the Terrorism (Protection of Premises) Act 2025:

- Scope checker (does the law apply to this premises?)
- Tier checker (standard duty vs enhanced duty)
- Duty mapping
- Procedural requirements checklist
- Action tracker
- Evidence pack
- Board-readiness summary

### Innovation 4: Role-Based Protective-Security Overlay
Dedicated insider / access-risk module based on **role exposure**, not just building condition. Directly aligned with NPSA role-based guidance on how role-linked access creates risk.

### Innovation 5: Guarding Substitution Intelligence
DRISK answers the commercial question every client has:

*Where can labour be replaced or reduced without breaching the protection baseline?*

Examples:
- Static guarding → mobile response
- Patrol frequency reduction after physical hardening
- Remote verification + response instead of full-time cover
- Scheduled uplift only during peak-risk windows

### Innovation 6: Assurance Confidence Score
Every output displays a confidence level. Score drops when:
- Evidence is weak
- Questions are unanswered
- Site plans are old
- Assessor competence is low
- Incident data is missing

Improves credibility and audit defensibility.

---

## EVIDENCE MANAGEMENT

Users can:
- Upload **photos, documents, and notes** directly to assessments
- Link evidence to **specific questions and findings**
- Attach evidence to **actions for verification**
- Maintain a **complete audit trail** of supporting documentation
- High-risk responses **automatically prompt evidence upload**
- Evidence can be attached to assessments, responses, or actions

---

## ACTION MANAGEMENT & TRACKING

DRISK converts assessment findings into tracked improvement actions:

**Action Fields:**
- Title
- Description
- Priority (low / medium / high / critical)
- Owner assignment
- Due date
- Status tracking
- Evidence linkage
- Residual-risk update after closure
- Comment / update history

**Action Status Workflow:**
- Open → In Progress → Blocked → Completed → Verified Closed

**Features:**
- Automatic flagging of overdue items
- Evidence required for closure verification
- Status change audit trail
- Owner notifications
- Linked directly to assessment findings

---

## 6 ASSESSMENT OUTPUTS

Every assessment produces six outputs:

### Output 1: Site Risk Summary (1-page operational picture)
- Headline risk score and band
- Top vulnerabilities
- Top recommendations
- Response concerns
- Next actions

### Output 2: Detailed Assessor Report
For risk and operations teams:
- Domain scores
- Evidence trail
- Control findings
- Asset-specific risks
- Scenario notes

### Output 3: Action Plan
- Owner
- Due date
- Evidence required
- Status
- Residual-risk effect after closure

### Output 4: Estate Dashboard
- Heatmap across all sites
- Risk trends over time
- High-risk sites flagged
- Overdue actions
- Recurring control failures

### Output 5: Executive Investment Paper
- Problem statement
- Current residual risk
- Investment options
- Expected risk reduction per option
- Compliance effect
- Cost comparison

### Output 6: Compliance / Assurance Pack
Built for: audit teams, insurers, regulators, client boards, or procurement teams.
- Evidence documentation
- Action history
- Policy alignment
- Audit-ready format

---

## 9 USER ROLES

DRISK supports nine roles with strict permission controls:

| Role | Primary Function |
|------|-----------------|
| System Administrator | Full system access, user and template management |
| Risk Consultant | Create and complete assessments, generate reports |
| Contract Manager | Review scores, manage actions, track progress |
| Supervisor | Operational oversight, patrol and procedure compliance |
| Client Security Lead | Client-side oversight of risk and actions |
| Executive / Board Viewer | Read-only access to dashboards and reports |
| Assessor | Complete structured site assessments, upload evidence |
| Action Owner | Manage and update assigned improvement actions |
| Auditor / Read-Only Reviewer | Read-only access for audit and compliance review |

Permissions must be strict, especially for evidence, asset detail, and role-based risk content.

---

## USER MANAGEMENT — 4 PRIMARY ACCESS TIERS

For simplicity in the MVP, the 9 roles map to 4 primary access tiers:

1. **Administrator** – Manage users, templates, system settings
2. **Assessor** – Create and complete assessments, upload evidence
3. **Contract Manager** – Review scores, manage actions, view reports
4. **Client Viewer** – View reports, site summaries, and actions (read-only)

---

## WORKFLOW MAP — 12-STAGE PROCESS

DRISK follows a continuous risk management cycle aligned with ISO 31000:

1. **Create estate and site profile**
2. **Set risk appetite and protection baseline**
3. **Run triage or standard assessment**
4. **Add site evidence and intelligence context**
5. **Calculate inherent, control, and residual risk**
6. **Identify weak, missing, and excessive controls**
7. **Generate options and optimisation recommendations**
8. **Create actions and assign owners**
9. **Feed actions into operations and assurance**
10. **Re-score after action closure**
11. **Track risk trend over time**
12. **Produce executive and compliance outputs**

---

## DATA MODEL & SYSTEM ARCHITECTURE

**Core Data Entities (18 entities):**

- **Users** – Platform users with login credentials
- **Roles** – Permission sets
- **Clients** – Organisations using DRISK
- **Estates** – Groups of related sites
- **Sites** – Individual physical locations
- **Assets** – Critical assets within sites (server rooms, reception, medicine stores, plant rooms, car parks, etc.)
- **Site Baseline** – Protection baseline per site
- **Assessment Templates** – Versioned blueprints for assessments
- **Assessment Domains** – 10 categories of questions
- **Assessment Questions** – Master question bank (~50 questions)
- **Assessments** – Individual site assessment instances
- **Assessment Responses** – Answers to individual questions
- **Evidence** – Supporting files (photos, documents, notes)
- **Risk Scores** – All calculated outputs
- **Actions** – Improvement tasks from findings
- **Action Updates** – Audit trail of action progress
- **Reports** – Generated assessment and summary reports
- **Recommendation Rules** – Logic behind generated actions
- **Audit Logs** – Complete system activity history

**Core Hierarchical Relationships:**

```
Client
├── Estate(s)
│   └── Site(s)
│       ├── Site Baseline
│       ├── Asset(s)
│       ├── Assessment(s)
│       │   ├── Response(s) → Question(s)
│       │   ├── Risk Score(s)
│       │   ├── Action(s)
│       │   └── Evidence
│       ├── Action(s)
│       └── Report(s)
└── User(s)
```

---

## CORE USER INTERFACE — 19 SCREENS (MVP)

### Primary Navigation:
Dashboard | Clients | Estates | Sites | Assessments | Actions | Reports | Admin

### All MVP Screens:
1. Login
2. Main Dashboard (total clients, sites, high-risk sites, overdue actions, recent assessments, upcoming reviews)
3. Client List (search, sector, sites, open actions, latest assessment)
4. Create / Edit Client
5. Estate List (name, client, region, number of sites)
6. Create / Edit Estate
7. Site List (filters: client, estate, type, risk band, review due)
8. Create / Edit Site
9. Site Profile (risk score, domain chart, vulnerabilities, open actions, sections: Assessments, Actions, Reports, Evidence)
10. Assessment List (ID, site, assessor, status, dates)
11. Create Assessment (site, template, type, assessor, date)
12. Assessment Screen (questions by domain, comment, upload, not applicable, save draft, next/previous)
13. Assessment Review / Summary (scores, risk band, chart, vulnerabilities, recommendations)
14. Action List (title, site, priority, owner, due date, status, overdue filter)
15. Action Detail (description, linked assessment, evidence, status updates, close action)
16. Report List
17. Report View / Export (site details, scores, vulnerabilities, action plan, export/print)
18. Admin Template / Question Management
19. User Management

### Critical User Journey:
Login → Dashboard → Site List → Site Profile → Start Assessment → Assessment Screen → Assessment Review → Create Actions → Generate Report

---

## FUNCTIONAL REQUIREMENTS

### 1. User Authentication and Access
- Secure login with email and password
- Role-based access control
- Session management and password reset
- User activity logging

### 2. Client and Site Management
- Create and edit clients (sector, contact, account manager)
- Create and edit estates (name, region, description)
- Create and edit sites (type, address, operating hours, occupancy, vulnerabilities, critical services)
- Track asset lists within sites

### 3. Assessment Management
- Create assessments linked to sites with template and type selection
- Save progress and resume later
- Auto-trigger scoring on completion
- Support four assessment types and tiered depth

### 4. Question and Response Handling
- Questions displayed grouped by domain
- Fixed wording and predefined answer options
- Optional comments, evidence upload, not-applicable option per question
- Enforce required fields before submission

### 5. Risk Scoring Engine
- Auto-calculate inherent risk, control effectiveness, response capability, residual risk
- Generate domain-level scores (all 10 domains)
- Calculate confidence score and optimisation status
- Produce compliance readiness indicator

### 6. Site Risk Dashboard
- Display overall risk score, band, domain chart, top vulnerabilities
- Show assessment history and trend comparison
- Display open actions, overdue flags, confidence score

### 7. Action Management
- Create, assign, track, and close improvement actions
- Link to assessments and site
- Flag overdue items automatically
- Audit trail of all status updates and evidence

### 8. Reporting
- Generate all 6 output types (summary, detailed, action plan, estate dashboard, executive paper, compliance pack)
- Export to printable / shareable formats
- Evidence attachable to reports

### 9. Reassessment and Trend Analysis
- Multiple assessments per site over time
- Compare assessments to show improvement or deterioration
- Risk trend charts and reduction metrics

### 10. Notifications and Reminders
- Action due date and overdue alerts
- Assessment review and reassessment reminders

---

## MVP SCOPE — PHASED PRODUCT ROADMAP

### V1 (MVP) — Must Have:
- Estate and site profiles
- Mobile and web assessment form (4 tiers)
- Photo and evidence capture
- Scoring engine (all 6 layers)
- Site and estate dashboards
- Action tracking
- Executive summary export
- Baseline / below / above protection view
- User roles and permissions
- Reassessment history

### V2 — Should Add:
- Scenario engine (event/threat-specific assessments)
- Live residual-risk triggers (CCTV faults, patrol failures, etc.)
- Cost-to-control optimiser
- Sector-specific templates
- Client benchmarking
- Operational workflow integration

### V3 — Future:
- Martyn's Law readiness workspace
- Role-based insider overlay (NPSA-aligned)
- Predictive trend modelling
- Insurer / broker compliance pack
- Advanced budget simulation
- AI-assisted narrative recommendations (with human approval)
- Full third-party integrations

---

## 6 PRIORITY SECTOR TEMPLATES

DRISK will build sector-specific assessment templates early to enter multiple markets:

1. **Healthcare** – NHS trusts, hospitals, clinics
2. **Education** – Universities and colleges
3. **Housing / Supported Accommodation** – Housing associations, shelters
4. **Council / Civic Estate** – Local authority buildings and services
5. **Logistics / Warehousing** – Distribution centres, depots
6. **Vacant Property** – Unoccupied buildings at elevated risk

---

## TECHNOLOGY STACK RECOMMENDATIONS

### Option A: Custom Build (Full Control)
- **Frontend:** React / Next.js
- **Backend:** Node.js / NestJS or Express
- **Database:** PostgreSQL
- **Authentication:** Supabase Auth, Auth0, or custom secure auth
- **File Storage:** Supabase Storage or AWS S3
- **Hosting:** AWS, Google Cloud, or Azure

### Option B: Fast MVP / Low-Code Hybrid (Recommended for Speed)
- **App Builder:** FlutterFlow, Bubble, or Retool
- **Backend / Database:** Supabase
- **Storage:** Supabase Storage
- **Auth:** Supabase Auth

**Smartest route:** Start with Option B to validate with clients, then rebuild with Option A after validation.

---

## COMMERCIAL MODEL — 3 TIERS

DRISK is offered in three commercial models:

### 1. Software-Only
For clients with their own teams who want the platform independently.

### 2. Managed Risk Service
Delta Force runs assessments and action governance on behalf of the client.

### 3. Risk-Plus-Operations
DRISK software **plus** guarding, mobile patrols, keyholding, audits, and improvement delivery.

**This third model is the strongest commercial moat** — no software-only provider can offer it.

---

## STRATEGIC DIFFERENTIATORS — 4 PILLARS

### A. Risk to Operations
Not just "identify the issue" — DRISK updates:
- Patrol plans
- Post instructions
- Escalation paths
- Supervisor frequencies
- Officer briefings

### B. Risk to Spend
Not just "fix it" — DRISK shows:
- Cheapest compliant option
- Best-value option
- Resilience-led option

### C. Risk to Evidence
Not just "we think we are secure" — DRISK provides:
- Documented findings
- Assigned actions
- Evidenced closures
- Trended improvement
- Reviewable history

### D. Risk to UK Readiness
DRISK is positioned as one of the easiest ways to prepare for UK protective-security expectations, including Martyn's Law preparation.

---

## KEY DIFFERENTIATORS — 10 POINTS

1. **Standardised Methodology** – Consistent framework across all sites and sectors
2. **Automated Scoring** – Removes subjective judgement from risk calculation
3. **Evidence-Based** – All findings backed by traceable documentation
4. **Operationally Grounded** – Built by security practitioners, not just software developers
5. **Actionable** – Converts findings into tracked improvement actions
6. **Comparable** – Sites and portfolios assessed on identical metrics
7. **Auditable** – Complete documentation and historical records
8. **Executive-Ready** – Reports suitable for board-level communication
9. **Scalable** – Works for single site or hundreds of locations
10. **Risk-Intelligent** – Optimisation score shows under/correctly/over-protected status

---

## STANDARDS & FRAMEWORK ALIGNMENT

DRISK is designed in alignment with established standards:

- **ISO 31000** – Risk management process (assess, treat, monitor, communicate)
- **ISO 22301** – Business continuity and resilience linkages
- **NPSA Role-Based Guidance** – Insider and role-linked access risk
- **ProtectUK** – Protective-security risk-management model (deter, detect, delay, respond)
- **Martyn's Law / Terrorism (Protection of Premises) Act 2025** – Duty of care and compliance readiness
- **Protective Security Risk Framework** – Inherent risk layered with controls and response

---

## STRATEGIC ADVANTAGES & CREDIBILITY

DRISK is credible because it's designed by **Delta Force Group**, a security operator that understands both sides of the problem:

**Operational Credibility:**
- Direct experience managing guarding, mobile patrols, keyholding, alarm response, compliance, and contract performance across multiple sectors
- Real-world knowledge of how controls actually perform in live environments
- Understanding of how recommendations must translate into workable operational plans
- Experience balancing protection with cost and service delivery
- Direct accountability for security outcomes in the field

**Strategic Advantage:**
- Not a theoretical reporting tool
- Built by people who understand site realities, client pressures, staffing models, and escalation requirements
- Designed to turn assessments into action, not just dashboards
- Links risk intelligence, compliance readiness, and operational delivery in one place

---

## BUSINESS OUTCOMES & ROI

DRISK delivers measurable outcomes:

- **Faster Visibility** – Know true security exposure in days, not months
- **Better Prioritisation** – Focus investment where it matters most
- **Proven Improvement** – Track risk reduction over time with hard data
- **Stronger Governance** – Document security decisions with evidence
- **Cost Optimisation** – Identify and eliminate wasted protective spend
- **Regulatory Confidence** – Demonstrate due diligence to auditors, insurers, and regulators
- **Portfolio Consistency** – Ensure minimum standards across all locations
- **Improved Safety** – Better protection across multiple sites
- **Evidence-Based Decisions** – Security spending justified by data, not opinion
- **Operational Efficiency** – Streamlined assessment and action tracking processes
- **Compliance Readiness** – Martyn's Law and duty-of-care documentation

---

## MVP ACCEPTANCE DEFINITION

The MVP is ready for pilot when a real user can:
- Log in
- Create a client and site
- Complete an assessment
- Attach evidence
- Receive calculated scores (all 6 layers)
- Create and manage actions
- Export a summary report
- Reassess the same site later

---

## BRAND LANGUAGE

Use wording like:
- Protective-security intelligence
- Live residual-risk visibility
- Evidence-led optimisation
- Operationally integrated risk management
- Martyn's Law readiness support
- Board-ready security decision support

**Avoid:** sounding like a generic software startup.

---

## SUMMARY

DRISK transforms how organisations manage physical security risk. By moving from fragmented, inconsistent, opinion-led assessments to structured, scored, evidence-based risk management, DRISK helps clients protect what matters most while making smarter investment decisions.

It is a platform built by security practitioners for security leaders — practical, credible, and designed to turn risk intelligence into action. The combination of 7 connected modules, 10 assessment domains, 6-layer risk scoring, innovation features including live risk triggers and Martyn's Law readiness, and 3-tier commercial model creates a comprehensive security intelligence platform that no software-only competitor can fully replicate.

**DRISK exists to answer one fundamental question: How do we make better, faster, more confident security decisions backed by data rather than opinion?**