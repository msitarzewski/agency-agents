# DRISK — Project Specification

**Source:** DRISK_Comprehensive_Summary.md, DRISK_UKPoliceAPI_Integration_Spec.md

---

## 1. MVP Scope Summary

### Screens (19 total)
- Login
- Main Dashboard (total clients, sites, high-risk sites, overdue actions, recent assessments, upcoming reviews)
- Client List (search, sector, sites, open actions, latest assessment)
- Create / Edit Client
- Estate List (name, client, region, number of sites)
- Create / Edit Estate
- Site List (filters: client, estate, type, risk band, review due)
- Create / Edit Site
- Site Profile (risk score, domain chart, vulnerabilities, open actions, sections: Assessments, Actions, Reports, Evidence)
- Assessment List (ID, site, assessor, status, dates)
- Create Assessment (site, template, type, assessor, date)
- Assessment Screen (questions by domain, comment, upload, not applicable, save draft, next/previous)
- Assessment Review / Summary (scores, risk band, chart, vulnerabilities, recommendations)
- Action List (title, site, priority, owner, due date, status, overdue filter)
- Action Detail (description, linked assessment, evidence, status updates, close action)
- Report List
- Report View / Export (site details, scores, vulnerabilities, action plan, export/print)
- Admin Template / Question Management
- User Management

### Modules (7)
1. **DRISK Profile** — Client, estate, site, asset baseline
2. **DRISK Assess** — Structured assessments (4 tiers)
3. **DRISK Intelligence** — External context (UK Police API)
4. **DRISK Score** — 6-layer scoring engine
5. **DRISK Act** — Action management
6. **DRISK Command** — Operational integration (out of MVP scope)
7. **DRISK Board** — Executive reporting

### Scoring Domains (10)
1. Site Context  
2. Asset Criticality  
3. External Threat Context  
4. Physical Protection  
5. Access Governance  
6. Human and Procedural Controls  
7. Response Capability  
8. Insider and Role-Based Exposure  
9. Resilience and Recovery  
10. Compliance and Assurance  

### Risk Scoring (6 layers)
- **Layer A:** Inherent Risk (Threat × Vulnerability × Impact)
- **Layer B:** Control Effectiveness
- **Layer C:** Response Capability
- **Layer D:** Residual Risk (Inherent × Control × Response multipliers)
- **Layer E:** Compliance Readiness
- **Layer F:** Optimisation Score

---

## 2. Tech Stack

**Required Stack — No Supabase**

- **Frontend:** Next.js (React)
- **Database:** PostgreSQL (direct connection — Prisma, Drizzle, or `pg`)
- **Auth:** NextAuth, Passport, or custom auth (no Supabase Auth)
- **Storage:** Local filesystem or S3-compatible storage (no Supabase Storage)
- **Hosting:** Vercel (or similar)

Do not use Supabase for auth or storage. Use direct PostgreSQL and custom auth from the start.

---

## 3. User Tiers (4)

| Tier | Primary Function |
|------|------------------|
| **Administrator** | Manage users, templates, system settings |
| **Assessor** | Create and complete assessments, upload evidence |
| **Contract Manager** | Review scores, manage actions, view reports |
| **Client Viewer** | View reports, site summaries, and actions (read-only) |

---

## 4. MVP Acceptance Criteria (Exact Quote)

> *"The MVP is ready for pilot when a real user can:*
> - *Log in*
> - *Create a client and site*
> - *Complete an assessment*
> - *Attach evidence*
> - *Receive calculated scores (all 6 layers)*
> - *Create and manage actions*
> - *Export a summary report*
> - *Reassess the same site later"*

---

## 5. UK Police API Integration (MVP Scope)

- **API:** data.police.uk (no auth, free)
- **MVP:** Store lat/lng on site; pull all-crime on site creation (background job); display crime count on Site Profile; pre-fill External Threat Q5/Q6; store in `site_crime_intelligence` table
- **Threat mapping:** 0–20 crimes = 1, 21–50 = 2, 51–100 = 3, 101–200 = 4, 200+ = 5

---

## 6. Core Data Entities

- Users, Roles, Clients, Estates, Sites, Assets
- Site Baseline, Assessment Templates, Domains, Questions
- Assessments, Responses, Evidence, Risk Scores
- Actions, Action Updates, Reports, Audit Logs

---

## 7. Critical User Journey

Login → Dashboard → Site List → Site Profile → Start Assessment → Assessment Screen → Assessment Review → Create Actions → Generate Report
