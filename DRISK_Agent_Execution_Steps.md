# DRISK Platform — Agent Execution Steps

**Purpose:** Build the DRISK (Digital Risk Intelligence for Security) platform using agency agents. Each step is designed to run in a **separate chat session** to avoid context window limits.

**Reference Documents:**
- `DRISK_Comprehensive_Summary.md` — Full product spec
- `DRISK_UKPoliceAPI_Integration_Spec.md` — UK Police API integration details

**How to run each step:** Open a new Cursor chat, attach the relevant files (e.g. `@DRISK_Comprehensive_Summary.md`), then paste the step prompt. The agent rules in `.cursor/rules/` are applied automatically when the prompt matches their domain.

---

## Agent Summary

| Phase | Agent(s) | Purpose |
|-------|----------|---------|
| 1 | Senior Project Manager | Create project spec + task list |
| 2 | ArchitectUX | Technical architecture + UX foundation |
| 3 | Backend Architect | Database schema, API design |
| 4 | Brand Guardian | Brand identity (optional, can merge with ArchitectUX) |
| 5 | Frontend Developer | App scaffold + core UI |
| 6 | Backend Architect + Frontend Developer | Auth, Client/Site CRUD |
| 7 | Backend Architect + Frontend Developer | Assessment engine + question bank |
| 8 | Backend Architect + AI Engineer | Risk scoring engine |
| 9 | Backend Architect | UK Police API integration |
| 10 | Frontend Developer | Dashboards, reports, actions |
| 11 | EvidenceQA | QA validation |
| 12 | Reality Checker | Final integration test |

**Total: ~12 steps, 6–8 distinct agent types**

---

## Pre-Step: Project Setup

Create the expected folder structure:

```bash
mkdir -p project-specs project-tasks project-docs
```

---

## Step 1: Project Specification & Task List

✅ **Status: Completed**

**Agent:** Senior Project Manager (rule: `senior-project-manager`)

**What to do:** In a new chat, run:

```
Read DRISK_Comprehensive_Summary.md and DRISK_UKPoliceAPI_Integration_Spec.md.

Create a project specification file at project-specs/drisk-setup.md that:
1. Summarizes the MVP scope (19 screens, 7 modules, 10 domains, 6-layer scoring)
2. Lists the tech stack (use: Next.js + PostgreSQL + custom auth — no Supabase)
3. Defines the 4 user tiers (Admin, Assessor, Contract Manager, Client Viewer)
4. Quotes exact MVP acceptance criteria from the summary

Then create a comprehensive task list at project-tasks/drisk-tasklist.md. Break the MVP into 20–30 implementable tasks. Each task should be completable in 30–60 minutes. Include:
- Task 1: Project scaffold (Next.js, DB, auth)
- Tasks 2–5: Client, Estate, Site CRUD
- Tasks 6–10: Assessment flow (create, questions, responses, evidence)
- Tasks 11–14: Risk scoring engine
- Tasks 15–17: UK Police API integration
- Tasks 18–22: Actions, Reports, Dashboards
- Tasks 23+: Admin, user management, polish

Quote EXACT requirements from the spec. Do not add luxury features.
```

**Outputs:**
- `project-specs/drisk-setup.md`
- `project-tasks/drisk-tasklist.md`

---

## Step 2: Technical Architecture & UX Foundation

✅ **Status: Completed**

**Agent:** ArchitectUX (rule: `ux-architect`)

**What to do:** In a new chat, run:

```
Read project-specs/drisk-setup.md and project-tasks/drisk-tasklist.md.

Create the technical architecture and UX foundation for the DRISK platform:

1. CSS design system (variables, typography, spacing, light/dark theme)
2. Layout framework (responsive breakpoints, grid patterns)
3. Information architecture for the 19 MVP screens
4. Component hierarchy and naming conventions
5. Theme toggle specification (light/dark/system)

Save deliverables to:
- project-docs/drisk-architecture.md
- css/design-system.css (or document in architecture)
- Include the 8 primary nav items: Dashboard | Clients | Estates | Sites | Assessments | Actions | Reports | Admin
```

**Outputs:**
- `project-docs/drisk-architecture.md`
- CSS/design system documentation

---

## Step 3: Database Schema & API Design

✅ **Status: Completed**

**Agent:** Backend Architect (rule: `backend-architect`)

**What to do:** In a new chat, run:

```
Read DRISK_Comprehensive_Summary.md (Data Model section) and project-specs/drisk-setup.md.

Design the DRISK database and API:

1. Create schema for all 18 core entities:
   Users, Roles, Clients, Estates, Sites, Assets, Site Baseline,
   Assessment Templates, Assessment Domains, Assessment Questions,
   Assessments, Assessment Responses, Evidence, Risk Scores,
   Actions, Action Updates, Reports, Audit Logs

2. Add site_crime_intelligence table per DRISK_UKPoliceAPI_Integration_Spec.md

3. Define API endpoints for:
   - Auth (login, session, password reset)
   - Clients CRUD
   - Estates CRUD (nested under client)
   - Sites CRUD (nested under estate)
   - Assessments CRUD
   - Actions CRUD
   - Reports generation

4. Document in project-docs/drisk-api-schema.md

Use PostgreSQL only. Do not use Supabase for auth or storage — implement custom auth (e.g., NextAuth, Passport) and local/S3-compatible storage.
```

**Outputs:**
- `project-docs/drisk-api-schema.md`
- SQL schema or Prisma/TypeORM schema

---

## Step 4: Project Scaffold & Auth

✅ **Status: Completed**

**Agent:** Rapid Prototyper or Frontend Developer + Backend Architect

> **DRISK does not use Supabase.** Use NextAuth, Passport, or custom auth with direct PostgreSQL (Prisma, Drizzle, or `pg`). If a previous scaffold mistakenly used Supabase, replace it entirely before proceeding.

**What to do:** In a new chat, run:

```
Read project-specs/drisk-setup.md and project-tasks/drisk-tasklist.md.

Implement Task 1 (Project scaffold):

1. Create Next.js 14 project with TypeScript
2. Set up PostgreSQL connection (direct connection — no Supabase client)
3. Implement authentication (NextAuth, Passport, or custom — no Supabase Auth):
   - Login, logout, session management
   - Password reset
   - Role-based access (4 tiers: Admin, Assessor, Contract Manager, Client Viewer)

4. Create base layout with navigation: Dashboard | Clients | Estates | Sites | Assessments | Actions | Reports | Admin

5. Apply ArchitectUX design system from project-docs/drisk-architecture.md

6. Create Login screen (screen 1 from MVP)

If the project was previously scaffolded with Supabase Auth or Supabase client, replace it entirely:
- Remove @supabase/supabase-js and Supabase Auth
- Add NextAuth (or Passport/custom auth)
- Use Prisma, Drizzle, or pg for direct PostgreSQL access

Mark Task 1 complete in project-tasks/drisk-tasklist.md when done.
```

**Outputs:**
- Next.js app with auth
- Login screen
- Base layout + nav

---

## Step 5: Client, Estate, Site CRUD (Completed)

**Agent:** Backend Architect + Frontend Developer

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md. Implement Tasks 2–5:

Task 2: Client List + Create/Edit Client (screens 3, 4)
Task 3: Estate List + Create/Edit Estate (screens 5, 6)
Task 4: Site List + Create/Edit Site (screens 7, 8)
Task 5: Site Profile screen (screen 9) — risk score placeholder, domain chart placeholder, sections: Assessments, Actions, Reports, Evidence

Include:
- Search and filters per spec
- Lat/lng storage on site for UK Police API (Phase 1)
- Asset list tracking within sites

Use project-docs/drisk-api-schema.md for API structure.
Mark tasks complete in task list when done.
```

**Outputs:**
- Client, Estate, Site CRUD
- Site Profile screen

---

## Step 6: Assessment Flow (Create, Questions, Responses)

**Agent:** Backend Architect + Frontend Developer

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md and DRISK_Comprehensive_Summary.md (Assessment section).

Implement Tasks 6–10:

Task 6: Assessment List + Create Assessment (screens 10, 11)
Task 7: Assessment Screen — questions grouped by domain (screen 12)
Task 8: Question bank — ~50 core questions across 10 domains, fixed wording, predefined options (1, 3, 5), weight, evidence requirement
Task 9: Response handling — save draft, comment, evidence upload, N/A option
Task 10: Assessment Review/Summary (screen 13) — scores placeholder, risk band, chart, vulnerabilities, recommendations

Support 4 assessment tiers: Rapid Triage, Standard, Enhanced, Scenario.
Use project-docs/drisk-api-schema.md.
Mark tasks complete when done.
```

**Outputs:**
- Assessment CRUD
- Question bank (10 domains)
- Assessment screen with domain grouping
- Assessment review/summary

---

## Step 7: Risk Scoring Engine

✅ **Status: Completed**

**Agent:** Backend Architect + AI Engineer (for scoring logic)

**What to do:** In a new chat, run:

```
Read DRISK_Comprehensive_Summary.md (Layered Risk Model, 10 Scoring Domains) and project-tasks/drisk-tasklist.md.

Implement Tasks 11–14 (Risk Scoring Engine):

1. Layer A: Inherent Risk = Threat × Vulnerability × Impact (1–5 each)
2. Layer B: Control Effectiveness (multiplier 0.6–1.0)
3. Layer C: Response Capability (multiplier 0.7–1.0)
4. Layer D: Residual Risk = Inherent × Control × Response
5. Layer E: Compliance Readiness
6. Layer F: Optimisation Score (under/correctly/over-protected)

7. Domain-level scores for all 10 domains
8. Confidence score (factors: unanswered questions, missing evidence)
9. Risk bands: 0–15 Low, 16–30 Moderate, 31–50 High, 51–75 Very High, 76+ Critical

Auto-trigger scoring on assessment completion.
Store in risk_scores table.
Mark tasks complete when done.
```

**Outputs:**
- Scoring engine logic
- Domain score calculation
- Risk band classification
- Confidence score

---

## Step 8: UK Police API Integration

**Agent:** Backend Architect

**What to do:** In a new chat, run:

```
Read DRISK_UKPoliceAPI_Integration_Spec.md and project-tasks/drisk-tasklist.md.

Implement Tasks 15–17 (UK Police API):

1. Create site_crime_intelligence table (schema in spec)
2. Background job on site creation: geocode address → lat/lng → call data.police.uk API
   - GET /api/crimes-street/all-crime?lat=&lng=&date=
   - Pull last 3 months
3. Map crime volumes to 1–5 threat score (table in spec)
4. Pre-fill External Threat domain Q5, Q6 from crime data
5. Display Crime Context panel on Site Profile: threat badge, monthly count, crime breakdown, data timestamp
6. Add disclaimer: "Crime data sourced from data.police.uk..."

Handle: 429 rate limit (exponential backoff), 503 (retry), no lat/lng (skip, show message).
Mark tasks complete when done.
```

**Outputs:**
- UK Police API integration
- site_crime_intelligence table + background job
- Crime Context panel on Site Profile
- Pre-fill for External Threat questions

---

## Step 9: Actions & Reports

**Agent:** Backend Architect + Frontend Developer

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md and DRISK_Comprehensive_Summary.md (Action Management, 6 Assessment Outputs).

Implement Tasks 18–22:

Task 18: Action List (screen 14) — title, site, priority, owner, due date, status, overdue filter
Task 19: Action Detail (screen 15) — description, linked assessment, evidence, status updates, close action
Task 20: Action workflow — Open → In Progress → Blocked → Completed → Verified Closed
Task 21: Report List + Report View/Export (screens 16, 17) — at minimum: Site Risk Summary (1-pager), Action Plan
Task 22: Main Dashboard (screen 2) — total clients, sites, high-risk sites, overdue actions, recent assessments, upcoming reviews

Mark tasks complete when done.
```

**Outputs:**
- Action CRUD + workflow
- Report generation (summary, action plan)
- Main Dashboard

---

## Step 10: Admin, User Management, Polish

**Agent:** Backend Architect + Frontend Developer

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md.

Implement remaining tasks:

Task 23: Admin Template/Question Management (screen 18)
Task 24: User Management (screen 19)
Task 25: Notifications — action due/overdue alerts, reassessment reminders
Task 26: Reassessment history — multiple assessments per site, trend comparison
Task 27: Polish — responsive design, accessibility (WCAG AA), error handling

Mark all tasks complete. Verify MVP acceptance:
- Log in ✓
- Create client and site ✓
- Complete assessment ✓
- Attach evidence ✓
- Receive calculated scores ✓
- Create and manage actions ✓
- Export summary report ✓
- Reassess same site later ✓
```

**Outputs:**
- Admin screens
- User management
- Notifications
- Full MVP completion

---

## Step 11: QA Validation

**Agent:** EvidenceQA (rule: `evidence-collector`)

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md and DRISK_Comprehensive_Summary.md (MVP Acceptance Definition).

The DRISK MVP is built. Perform QA validation:

1. Run: ./qa-playwright-capture.sh http://localhost:3000 public/qa-screenshots
   (or equivalent for your dev server URL)

2. Test critical user journey:
   Login → Dashboard → Site List → Site Profile → Start Assessment → Assessment Screen → Assessment Review → Create Actions → Generate Report

3. Verify each MVP screen renders and functions
4. Check responsive (desktop, tablet, mobile)
5. Check theme toggle (light/dark/system)
6. Document issues with screenshot evidence
7. Provide PASS/FAIL with specific feedback

Default to finding issues. First implementations typically have 3–5+ issues.
```

**Outputs:**
- QA report with screenshots
- Issue list with evidence
- PASS/FAIL decision

---

## Step 12: Final Integration & Reality Check

**Agent:** Reality Checker (rule: `reality-checker`)

**What to do:** In a new chat, run:

```
Read project-tasks/drisk-tasklist.md, QA findings from Step 11, and DRISK_Comprehensive_Summary.md.

Perform final integration testing on the DRISK MVP:

1. Cross-validate QA findings
2. Test complete user journeys end-to-end
3. Verify specification compliance
4. Check: Login, Client/Site CRUD, Assessment flow, Scoring, UK Police API display, Actions, Reports, Dashboard
5. Default to NEEDS WORK unless overwhelming evidence proves production readiness
6. Provide realistic quality assessment (C+/B-/B/B+)
7. List required fixes before production consideration
```

**Outputs:**
- Integration report
- Production readiness assessment
- Remediation list

---

## Execution Order Summary

| Step | Agent | Chat Focus |
|------|-------|------------|
| 1 | Senior Project Manager | Spec + task list |
| 2 | ArchitectUX | Architecture + UX |
| 3 | Backend Architect | DB + API design |
| 4 | Rapid Prototyper / Frontend + Backend | Scaffold + auth |
| 5 | Backend + Frontend | Client, Estate, Site CRUD |
| 6 | Backend + Frontend | Assessment flow |
| 7 | Backend + AI Engineer | Scoring engine |
| 8 | Backend Architect | UK Police API |
| 9 | Backend + Frontend | Actions, Reports, Dashboard |
| 10 | Backend + Frontend | Admin, users, polish |
| 11 | EvidenceQA | QA validation |
| 12 | Reality Checker | Final integration |

---

## Tips for Running Steps

1. **Start each step in a fresh chat** — paste the step prompt and attach the relevant files (`@DRISK_Comprehensive_Summary.md`, `@project-tasks/drisk-tasklist.md`, etc.).

2. **Pass context explicitly** — e.g. "Continue from Step 5. Task list is at project-tasks/drisk-tasklist.md. Tasks 2–5 are complete."

3. **Verify outputs before next step** — ensure files are created and tasks are marked complete.

4. **If a step fails** — re-run with the same agent, include QA feedback or error details. Max 3 retries per orchestrator rules.

5. **Tech stack** — Use Next.js + PostgreSQL + custom auth (NextAuth, Passport, etc.). Do not use Supabase for auth or storage.

---

## File Locations Reference

| File | Purpose |
|------|---------|
| `project-specs/drisk-setup.md` | Project specification (created Step 1) |
| `project-tasks/drisk-tasklist.md` | Task list with checkboxes (created Step 1) |
| `project-docs/drisk-architecture.md` | Technical architecture (created Step 2) |
| `project-docs/drisk-api-schema.md` | DB schema + API design (created Step 3) |
| `DRISK_Comprehensive_Summary.md` | Full product spec (existing) |
| `DRISK_UKPoliceAPI_Integration_Spec.md` | UK Police API spec (existing) |

---

*Generated for DRISK platform build. Run steps sequentially in separate chats.*
