# DRISK MVP — Development Task List

**Specification Reference:** project-specs/drisk-setup.md  
**Original Requirements:** DRISK_Comprehensive_Summary.md, DRISK_UKPoliceAPI_Integration_Spec.md

---

## Specification Summary

**MVP Acceptance Criteria (exact quote):**  
*"The MVP is ready for pilot when a real user can: Log in; Create a client and site; Complete an assessment; Attach evidence; Receive calculated scores (all 6 layers); Create and manage actions; Export a summary report; Reassess the same site later."*

**Tech Stack:** Next.js + PostgreSQL + custom auth (NextAuth/Passport) — no Supabase  
**Scope:** 19 screens, 7 modules, 10 domains, 6-layer scoring

---

## Development Tasks

### [x] Task 1: Project Scaffold
**Description:** Set up Next.js project with direct PostgreSQL and custom auth (NextAuth, Passport, or custom).  
**Acceptance Criteria:**
- Next.js app with App Router
- Direct PostgreSQL connection (Prisma, Drizzle, or `pg` — no Supabase client)
- Auth: NextAuth, Passport, or custom (email/password login — no Supabase Auth)
- Session management and protected routes
- Basic layout with navigation shell

**Files:** `package.json`, `next.config.js`, auth middleware, DB client (Prisma/Drizzle/pg)  
**Reference:** Tech stack in drisk-setup.md

---

### [x] Task 2: Database Schema — Core Entities
**Description:** Create PostgreSQL schema for Clients, Estates, Sites, Users, Roles.  
**Acceptance Criteria:**
- `clients` table (sector, contact, account manager)
- `estates` table (name, region, description, client_id)
- `sites` table (type, address, lat, lng, operating_hours, occupancy, estate_id)
- `users` and `roles` tables with RLS policies
- Foreign keys and indexes

**Reference:** Core Data Entities in DRISK_Comprehensive_Summary.md

---

### [x] Task 3: Client CRUD
**Description:** Implement Client List and Create/Edit Client screens.  
**Acceptance Criteria:**
- Client List with search, sector filter, sites count, open actions, latest assessment
- Create Client form (sector, contact, account manager)
- Edit Client
- Delete or soft-delete Client

**Screens:** 3, 4  
**Reference:** Client and Site Management requirements

---

### [x] Task 4: Estate CRUD
**Description:** Implement Estate List and Create/Edit Estate screens.  
**Acceptance Criteria:**
- Estate List (name, client, region, number of sites)
- Create Estate (name, region, description, client)
- Edit Estate

**Screens:** 5, 6  
**Reference:** Client and Site Management requirements

---

### [x] Task 5: Site CRUD
**Description:** Implement Site List, Create/Edit Site, and Site Profile screens.  
**Acceptance Criteria:**
- Site List with filters (client, estate, type, risk band, review due)
- Create Site (type, address, lat/lng, operating hours, occupancy, vulnerabilities, critical services)
- Edit Site
- Site Profile with risk score placeholder, domain chart placeholder, vulnerabilities, open actions, sections for Assessments, Actions, Reports, Evidence

**Screens:** 7, 8, 9  
**Reference:** Site Management, Site Profile in spec

---

### [x] Task 6: Assessment Template & Question Bank
**Description:** Create assessment templates, 10 domains, and ~50 core questions.  
**Acceptance Criteria:**
- `assessment_templates`, `assessment_domains`, `assessment_questions` tables
- Seed 10 domains and ~50 questions with fixed wording, predefined options (1/3/5), weight (1–4), evidence requirement
- Admin screen for template/question management (basic)

**Reference:** 10 Scoring Domains, Structured Assessment Question Bank

---

### [x] Task 7: Create Assessment Flow
**Description:** Implement Create Assessment and Assessment List screens.  
**Acceptance Criteria:**
- Create Assessment (site, template, type, assessor, date)
- Assessment List (ID, site, assessor, status, dates)
- Link assessment to site and template

**Screens:** 10, 11  
**Reference:** Assessment Management requirements

---

### [x] Task 8: Assessment Screen — Question Display
**Description:** Build Assessment Screen with questions grouped by domain.  
**Acceptance Criteria:**
- Questions displayed by domain
- Fixed wording and predefined answer options (1, 3, 5)
- Next/previous navigation
- Save draft
- Optional comment and "not applicable" per question

**Screen:** 12  
**Reference:** Question and Response Handling

---

### [x] Task 9: Assessment Responses & Evidence Upload
**Description:** Persist responses and support evidence upload.  
**Acceptance Criteria:**
- Save responses to `assessment_responses`
- Upload photos/documents to local storage or S3-compatible storage (no Supabase)
- Link evidence to questions and findings
- High-risk responses prompt evidence upload
- Enforce required fields before submission

**Reference:** Evidence Management, Question and Response Handling

---

### [x] Task 10: Assessment Completion & Auto-Score Trigger
**Description:** Complete assessment flow and trigger scoring on submission.  
**Acceptance Criteria:**
- Submit assessment (validate required fields)
- Auto-trigger scoring engine on completion
- Assessment status: draft → completed

**Reference:** Assessment Management — "Auto-trigger scoring on completion"

---

### [x] Task 11: Risk Scoring Engine — Layers A–D
**Description:** Implement inherent risk, control effectiveness, response capability, residual risk.  
**Acceptance Criteria:**
- Layer A: Inherent Risk = Threat × Vulnerability × Impact (1–5 each)
- Layer B: Control Effectiveness multiplier (0.6 / 0.8 / 1.0)
- Layer C: Response Capability multiplier (0.7 / 0.85 / 1.0)
- Layer D: Residual Risk = Inherent × Control × Response
- Store scores in `risk_scores` table

**Reference:** Layered Risk Model — 6 Layers

---

### [x] Task 12: Risk Scoring Engine — Domain Scores
**Description:** Calculate domain-level scores across 10 domains.  
**Acceptance Criteria:**
- Map question responses to domain scores
- Weighted score = Base Score × Question Weight
- Produce domain-level breakdown for chart

**Reference:** 10 Scoring Domains, Question Weight Scale

---

### [x] Task 13: Risk Scoring Engine — Layers E & F, Confidence
**Description:** Add compliance readiness, optimisation score, confidence score.  
**Acceptance Criteria:**
- Layer E: Compliance Readiness (policy, training, action closure, audit)
- Layer F: Optimisation Score (under/correctly/over-protected)
- Confidence score (90–100% high, 70–89% medium, &lt;70% low)
- Risk bands: 0–15 Low, 16–30 Moderate, 31–50 High, 51–75 Very High, 76+ Critical

**Reference:** Layers E & F, Confidence Score, Risk Bands

---

### [x] Task 14: Site Risk Dashboard Integration
**Description:** Display scores on Site Profile and Dashboard.  
**Acceptance Criteria:**
- Site Profile shows overall risk score, band, domain chart, top vulnerabilities
- Assessment history and trend comparison
- Open actions, overdue flags, confidence score
- Main Dashboard: total clients, sites, high-risk sites, overdue actions, recent assessments, upcoming reviews

**Screens:** 2, 9  
**Reference:** Site Risk Dashboard, Main Dashboard

---

### [ ] Task 15: UK Police API — Site Creation Hook
**Description:** Geocode site and queue crime data fetch on site creation.  
**Acceptance Criteria:**
- Store lat/lng on site (geocode from address or manual entry)
- Background job to call `GET /api/crimes-street/all-crime` for last 3 months
- Create `site_crime_intelligence` table
- Handle sites without lat/lng (skip API, show message)

**Reference:** DRISK_UKPoliceAPI_Integration_Spec — Step 1, Data Storage

---

### [ ] Task 16: UK Police API — Threat Score Mapping
**Description:** Map crime volumes to 1–5 threat score and pre-fill External Threat.  
**Acceptance Criteria:**
- Aggregate crime counts by category (violent, ASB, burglary, disorder, etc.)
- Map to threat score: 0–20=1, 21–50=2, 51–100=3, 101–200=4, 200+=5
- Pre-fill External Threat Q5 and Q6 in assessment
- Display crime count and threat badge on Site Profile
- Data timestamp: "Based on UK Police data — last updated [month]"

**Reference:** Threat Score Mapping, Pre-fill Q5/Q6

---

### [ ] Task 17: UK Police API — Error Handling & Disclaimer
**Description:** Handle API errors and display required disclaimer.  
**Acceptance Criteria:**
- 429: Retry with exponential backoff (max 3)
- 503: Queue retry in 1 hour
- Empty results: "No crime data available" — assessor answers manually
- UI disclaimer: "Crime data sourced from data.police.uk. Locations are approximated..."

**Reference:** Error Handling, Security & Compliance Notes

---

### [ ] Task 18: Action Management — Create & List
**Description:** Implement Action List and create actions from assessment findings.  
**Acceptance Criteria:**
- Action List (title, site, priority, owner, due date, status, overdue filter)
- Create actions from assessment (title, description, priority, owner, due date)
- Link to assessment and site
- Status: Open → In Progress → Blocked → Completed → Verified Closed

**Screens:** 14  
**Reference:** Action Management & Tracking

---

### [ ] Task 19: Action Detail & Updates
**Description:** Implement Action Detail screen with status updates and evidence.  
**Acceptance Criteria:**
- Action Detail (description, linked assessment, evidence, status updates, close action)
- Evidence required for closure verification
- Audit trail of status changes
- Overdue flagging

**Screen:** 15  
**Reference:** Action Management & Tracking

---

### [ ] Task 20: Reports — List & Summary Export
**Description:** Implement Report List and Site Risk Summary export.  
**Acceptance Criteria:**
- Report List
- Generate Site Risk Summary (1-page: headline score, band, top vulnerabilities, top recommendations, response concerns, next actions)
- Export to printable/shareable format (PDF or HTML)

**Screens:** 16, 17  
**Reference:** 6 Assessment Outputs — Output 1

---

### [ ] Task 21: Reports — Action Plan & Export
**Description:** Add Action Plan to reports and export.  
**Acceptance Criteria:**
- Action Plan in report (owner, due date, evidence required, status, residual-risk effect)
- Export includes action plan
- Evidence attachable to reports

**Reference:** Output 3, Reporting requirements

---

### [ ] Task 22: Estate Dashboard & Heatmap
**Description:** Implement estate-level dashboard with heatmap.  
**Acceptance Criteria:**
- Estate heatmap across all sites
- Risk trends over time
- High-risk sites flagged
- Overdue actions summary

**Reference:** Output 4 — Estate Dashboard

---

### [ ] Task 23: User Management & Roles
**Description:** Implement User Management screen and role-based access.  
**Acceptance Criteria:**
- User Management screen (create, edit, assign role)
- 4 tiers: Administrator, Assessor, Contract Manager, Client Viewer
- Permission checks on routes and actions
- User activity logging (basic)

**Screen:** 19  
**Reference:** 4-Tier Assessment Structure, User Management

---

### [ ] Task 24: Admin Template & Question Management
**Description:** Complete Admin screen for templates and questions.  
**Acceptance Criteria:**
- View/edit assessment templates
- View/edit domains and questions
- Question fields: wording, options, weight, evidence requirement

**Screen:** 18  
**Reference:** Admin Template / Question Management

---

### [ ] Task 25: Reassessment & Trend Comparison
**Description:** Support multiple assessments per site and trend comparison.  
**Acceptance Criteria:**
- Multiple assessments per site over time
- Compare assessments (improvement/deterioration)
- Risk trend charts on Site Profile
- Reassess same site flow

**Reference:** MVP Acceptance — "Reassess the same site later", Reassessment and Trend Analysis

---

### [ ] Task 26: Notifications & Reminders (Basic)
**Description:** Action due date and overdue alerts.  
**Acceptance Criteria:**
- Overdue action flagging on Dashboard and Action List
- Assessment review / reassessment reminders (in-app or email — basic)

**Reference:** Notifications and Reminders

---

### [ ] Task 27: Polish & QA
**Description:** End-to-end testing and polish.  
**Acceptance Criteria:**
- Full critical journey works: Login → Dashboard → Site List → Site Profile → Start Assessment → Assessment Screen → Assessment Review → Create Actions → Generate Report
- Responsive layout
- Error states and loading states
- No luxury features — only spec requirements

**Reference:** Critical User Journey, MVP Acceptance Criteria

---

## Quality Requirements

- [ ] All CRUD operations use direct PostgreSQL (Prisma, Drizzle, or `pg`) — no Supabase client
- [ ] No background processes appended with `&` — use serverless jobs, cron, or queue (e.g., Vercel Cron, BullMQ)
- [ ] Mobile-responsive design
- [ ] Form validation and error handling
- [ ] Images from approved sources (Unsplash, picsum.photos) — NO Pexels

---

## Technical Notes

**Development Stack:** Next.js 14+, PostgreSQL (direct), custom auth (NextAuth/Passport), local/S3 storage  
**Special Instructions:** Quote exact requirements from spec; do not add luxury features  
**Timeline:** 20–30 tasks × 30–60 min each ≈ 10–30 hours development
