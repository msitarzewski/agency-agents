# DRISK Database Schema — 18 Core Entities

**Source:** DRISK_Comprehensive_Summary.md (Data Model section), project-specs/drisk-setup.md

**Database:** PostgreSQL

---

## Entity Overview

| # | Entity | Description |
|---|--------|-------------|
| 1 | users | Platform users with login credentials |
| 2 | roles | Permission sets |
| 3 | clients | Organisations using DRISK |
| 4 | estates | Groups of related sites |
| 5 | sites | Individual physical locations |
| 6 | assets | Critical assets within sites |
| 7 | site_baselines | Protection baseline per site |
| 8 | assessment_templates | Versioned blueprints for assessments |
| 9 | assessment_domains | 10 categories of questions |
| 10 | assessment_questions | Master question bank (~50 questions) |
| 11 | assessments | Individual site assessment instances |
| 12 | assessment_responses | Answers to individual questions |
| 13 | evidence | Supporting files (photos, documents, notes) |
| 14 | risk_scores | All calculated outputs |
| 15 | actions | Improvement tasks from findings |
| 16 | action_updates | Audit trail of action progress |
| 17 | reports | Generated assessment and summary reports |
| 18 | audit_logs | Complete system activity history |
| 19 | site_crime_intelligence | UK Police API crime data per site (External Threat) |

---

## SQL Schema

```sql
-- =============================================================================
-- DRISK Database Schema — 18 Core Entities
-- PostgreSQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ROLES
-- -----------------------------------------------------------------------------
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3, 4)), -- 1=Admin, 2=Assessor, 3=Contract Manager, 4=Client Viewer
  permissions JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 2. CLIENTS (before users: users.client_id references clients)
-- -----------------------------------------------------------------------------
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  sector VARCHAR(100),
  contact_name VARCHAR(200),
  contact_email VARCHAR(255),
  contact_phone VARCHAR(50),
  account_manager_id UUID, -- FK added after users exists
  risk_appetite TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 3. USERS
-- -----------------------------------------------------------------------------
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  role_id UUID NOT NULL REFERENCES roles(id),
  client_id UUID REFERENCES clients(id), -- nullable: admins/assessors may not be client-bound
  is_active BOOLEAN DEFAULT true,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add FK for clients.account_manager_id after users exists
ALTER TABLE clients ADD CONSTRAINT fk_clients_account_manager FOREIGN KEY (account_manager_id) REFERENCES users(id);

-- -----------------------------------------------------------------------------
-- 4. ESTATES
-- -----------------------------------------------------------------------------
CREATE TABLE estates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  region VARCHAR(100),
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_estates_client ON estates(client_id);

-- -----------------------------------------------------------------------------
-- 5. SITES
-- -----------------------------------------------------------------------------
CREATE TABLE sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  estate_id UUID NOT NULL REFERENCES estates(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  site_type VARCHAR(100),
  address_line1 VARCHAR(255),
  address_line2 VARCHAR(255),
  city VARCHAR(100),
  postcode VARCHAR(20),
  country VARCHAR(100) DEFAULT 'UK',
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  operating_hours TEXT,
  occupancy_profile TEXT,
  public_access_level VARCHAR(50),
  vulnerable_occupants TEXT,
  critical_services TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sites_estate ON sites(estate_id);
CREATE INDEX idx_sites_coords ON sites(latitude, longitude);

-- -----------------------------------------------------------------------------
-- 6. ASSETS
-- -----------------------------------------------------------------------------
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  asset_type VARCHAR(100), -- server room, reception, medicine store, plant room, car park, etc.
  description TEXT,
  criticality_level INTEGER CHECK (criticality_level BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assets_site ON assets(site_id);

-- -----------------------------------------------------------------------------
-- 7. SITE BASELINES
-- -----------------------------------------------------------------------------
CREATE TABLE site_baselines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE UNIQUE,
  protection_level VARCHAR(50),
  baseline_controls JSONB DEFAULT '{}',
  required_response_standards TEXT,
  legal_requirements TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_site_baselines_site ON site_baselines(site_id);

-- -----------------------------------------------------------------------------
-- 8. ASSESSMENT TEMPLATES
-- -----------------------------------------------------------------------------
CREATE TABLE assessment_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  version VARCHAR(50) NOT NULL,
  tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3, 4)), -- 1=Rapid, 2=Standard, 3=Enhanced, 4=Scenario
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, version)
);

-- -----------------------------------------------------------------------------
-- 9. ASSESSMENT DOMAINS
-- -----------------------------------------------------------------------------
CREATE TABLE assessment_domains (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES assessment_templates(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  domain_number INTEGER NOT NULL, -- 1-10
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessment_domains_template ON assessment_domains(template_id);

-- -----------------------------------------------------------------------------
-- 10. ASSESSMENT QUESTIONS
-- -----------------------------------------------------------------------------
CREATE TABLE assessment_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain_id UUID NOT NULL REFERENCES assessment_domains(id) ON DELETE CASCADE,
  question_text TEXT NOT NULL,
  question_number VARCHAR(20),
  weight INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 4),
  answer_options JSONB NOT NULL, -- [{label, score}, ...]
  evidence_requirement TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessment_questions_domain ON assessment_questions(domain_id);

-- -----------------------------------------------------------------------------
-- 11. ASSESSMENTS
-- -----------------------------------------------------------------------------
CREATE TABLE assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  template_id UUID NOT NULL REFERENCES assessment_templates(id),
  assessor_id UUID NOT NULL REFERENCES users(id),
  status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, in_progress, completed
  assessment_type VARCHAR(50), -- rapid, standard, enhanced, scenario
  assessed_at DATE,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessments_site ON assessments(site_id);
CREATE INDEX idx_assessments_assessor ON assessments(assessor_id);
CREATE INDEX idx_assessments_status ON assessments(status);

-- -----------------------------------------------------------------------------
-- 12. ASSESSMENT RESPONSES
-- -----------------------------------------------------------------------------
CREATE TABLE assessment_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES assessment_questions(id) ON DELETE CASCADE,
  selected_score INTEGER, -- 1, 3, or 5
  comment TEXT,
  is_not_applicable BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(assessment_id, question_id)
);

CREATE INDEX idx_assessment_responses_assessment ON assessment_responses(assessment_id);
CREATE INDEX idx_assessment_responses_question ON assessment_responses(question_id);

-- -----------------------------------------------------------------------------
-- 13. EVIDENCE (action_id FK added after actions exists)
-- -----------------------------------------------------------------------------
CREATE TABLE evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  response_id UUID REFERENCES assessment_responses(id) ON DELETE CASCADE,
  action_id UUID, -- FK added after actions exists
  file_type VARCHAR(50), -- photo, document, note
  file_url TEXT NOT NULL,
  file_name VARCHAR(255),
  description TEXT,
  uploaded_by_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_assessment ON evidence(assessment_id);
CREATE INDEX idx_evidence_response ON evidence(response_id);
CREATE INDEX idx_evidence_action ON evidence(action_id);

-- -----------------------------------------------------------------------------
-- 14. RISK SCORES
-- -----------------------------------------------------------------------------
CREATE TABLE risk_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  layer VARCHAR(50) NOT NULL, -- inherent, control, response, residual, compliance, optimisation
  domain_id UUID REFERENCES assessment_domains(id),
  score_value DECIMAL(10, 8),
  band VARCHAR(50), -- low, moderate, high, very_high, critical
  multiplier DECIMAL(5, 4),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_scores_assessment ON risk_scores(assessment_id);
CREATE INDEX idx_risk_scores_layer ON risk_scores(layer);

-- -----------------------------------------------------------------------------
-- 15. ACTIONS
-- -----------------------------------------------------------------------------
CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  priority VARCHAR(50) NOT NULL,
  owner_id UUID REFERENCES users(id),
  due_date DATE,
  status VARCHAR(50) NOT NULL DEFAULT 'open',
  residual_risk_after_closure DECIMAL(10, 8),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ,
  created_by_id UUID REFERENCES users(id)
);

CREATE INDEX idx_actions_site ON actions(site_id);
CREATE INDEX idx_actions_assessment ON actions(assessment_id);
CREATE INDEX idx_actions_owner ON actions(owner_id);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_due_date ON actions(due_date);

-- Add FK for evidence.action_id (deferred: evidence created before actions)
ALTER TABLE evidence ADD CONSTRAINT fk_evidence_action FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE;

-- -----------------------------------------------------------------------------
-- 16. ACTION UPDATES
-- -----------------------------------------------------------------------------
CREATE TABLE action_updates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id UUID NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id),
  previous_status VARCHAR(50),
  new_status VARCHAR(50) NOT NULL,
  comment TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_action_updates_action ON action_updates(action_id);

-- -----------------------------------------------------------------------------
-- 17. REPORTS
-- -----------------------------------------------------------------------------
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
  assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
  report_type VARCHAR(100) NOT NULL,
  title VARCHAR(255),
  content JSONB,
  file_url TEXT,
  generated_by_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_site ON reports(site_id);
CREATE INDEX idx_reports_assessment ON reports(assessment_id);
CREATE INDEX idx_reports_type ON reports(report_type);

-- -----------------------------------------------------------------------------
-- 18. AUDIT LOGS
-- -----------------------------------------------------------------------------
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  entity_type VARCHAR(100),
  entity_id UUID,
  action VARCHAR(50) NOT NULL,
  changes JSONB,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- -----------------------------------------------------------------------------
-- 19. SITE CRIME INTELLIGENCE (UK Police API integration)
-- -----------------------------------------------------------------------------
CREATE TABLE site_crime_intelligence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  data_month VARCHAR(7) NOT NULL, -- YYYY-MM
  total_crimes INTEGER DEFAULT 0,
  violent_crimes INTEGER DEFAULT 0,
  asb_count INTEGER DEFAULT 0,
  burglary_count INTEGER DEFAULT 0,
  disorder_count INTEGER DEFAULT 0,
  vehicle_crime_count INTEGER DEFAULT 0,
  drug_count INTEGER DEFAULT 0,
  calculated_threat_score INTEGER CHECK (calculated_threat_score BETWEEN 1 AND 5),
  raw_response JSONB DEFAULT '{}',
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  data_source VARCHAR(100) DEFAULT 'uk-police-api',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(site_id, data_month)
);

CREATE INDEX idx_site_crime_intelligence_site ON site_crime_intelligence(site_id);
CREATE INDEX idx_site_crime_intelligence_month ON site_crime_intelligence(data_month);
```

---

## Schema Creation Order (Circular Dependencies)

The SQL above is ordered to run top-to-bottom. Circular references are handled with deferred `ALTER TABLE`:

| Circular ref | Resolution |
|--------------|------------|
| `users.client_id` ↔ `clients.account_manager_id` | Create **clients** first (no account_manager_id FK), then **users**, then `ALTER clients` add FK to users |
| `evidence.action_id` ↔ `actions` | Create **evidence** with `action_id UUID` (no FK), then **actions**, then `ALTER evidence` add FK |

Creation order: roles → clients → users → [ALTER clients] → estates → sites → assets → site_baselines → assessment_templates → assessment_domains → assessment_questions → assessments → assessment_responses → evidence → risk_scores → actions → [ALTER evidence] → action_updates → reports → audit_logs → site_crime_intelligence

---

## Hierarchical Relationships

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
│       └── Site Crime Intelligence (per site)
└── User(s)
```

---

## API Design

**Base URL:** `/api` (or `/api/v1`)

**Authentication:** Session-based (cookies) or Bearer token. All endpoints except auth require authentication.

---

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Authenticate user |
| GET | `/api/auth/session` | Get current session |
| POST | `/api/auth/logout` | End session |
| POST | `/api/auth/password-reset/request` | Request password reset email |
| POST | `/api/auth/password-reset/confirm` | Confirm reset with token |

**POST /api/auth/login**

Request:
```json
{
  "email": "string",
  "password": "string"
}
```

Response (200):
```json
{
  "user": {
    "id": "uuid",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": { "id": "uuid", "name": "string", "tier": 1 },
    "client_id": "uuid | null"
  },
  "session": { "expires_at": "ISO8601" }
}
```

**GET /api/auth/session**

Response (200):
```json
{
  "user": { "id": "uuid", "email": "string", "first_name": "string", "last_name": "string", "role": { "id": "uuid", "name": "string", "tier": 1 }, "client_id": "uuid | null" },
  "expires_at": "ISO8601"
}
```

**POST /api/auth/password-reset/request**

Request:
```json
{ "email": "string" }
```

Response (200):
```json
{ "message": "If an account exists, a reset link has been sent." }
```

**POST /api/auth/password-reset/confirm**

Request:
```json
{
  "token": "string",
  "new_password": "string"
}
```

Response (200):
```json
{ "message": "Password has been reset." }
```

---

### Clients CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clients` | List clients (paginated) |
| GET | `/api/clients/:id` | Get client by ID |
| POST | `/api/clients` | Create client |
| PATCH | `/api/clients/:id` | Update client |
| DELETE | `/api/clients/:id` | Delete client |

**GET /api/clients**

Query: `?page=1&limit=20&search=`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "string",
      "sector": "string",
      "contact_name": "string",
      "contact_email": "string",
      "contact_phone": "string",
      "account_manager_id": "uuid | null",
      "risk_appetite": "string",
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/clients/:id**

Response (200):
```json
{
  "id": "uuid",
  "name": "string",
  "sector": "string",
  "contact_name": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "account_manager_id": "uuid | null",
  "risk_appetite": "string",
  "estates": [{ "id": "uuid", "name": "string", "region": "string" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**POST /api/clients**

Request:
```json
{
  "name": "string",
  "sector": "string",
  "contact_name": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "account_manager_id": "uuid | null",
  "risk_appetite": "string"
}
```

Response (201): Same shape as GET /api/clients/:id

**PATCH /api/clients/:id**

Request: Partial object (same fields as POST)

Response (200): Same shape as GET /api/clients/:id

**DELETE /api/clients/:id**

Response (204): No content

---

### Estates CRUD (nested under client)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clients/:clientId/estates` | List estates for client |
| GET | `/api/estates/:id` | Get estate by ID |
| POST | `/api/clients/:clientId/estates` | Create estate |
| PATCH | `/api/estates/:id` | Update estate |
| DELETE | `/api/estates/:id` | Delete estate |

**GET /api/clients/:clientId/estates**

Query: `?page=1&limit=20`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "name": "string",
      "region": "string",
      "description": "string",
      "site_count": 0,
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/estates/:id**

Response (200):
```json
{
  "id": "uuid",
  "client_id": "uuid",
  "name": "string",
  "region": "string",
  "description": "string",
  "sites": [{ "id": "uuid", "name": "string", "site_type": "string", "city": "string", "postcode": "string" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**POST /api/clients/:clientId/estates**

Request:
```json
{
  "name": "string",
  "region": "string",
  "description": "string"
}
```

Response (201): Same shape as GET /api/estates/:id

**PATCH /api/estates/:id**

Request: Partial object

Response (200): Same shape as GET /api/estates/:id

**DELETE /api/estates/:id**

Response (204): No content

---

### Sites CRUD (nested under estate)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/estates/:estateId/sites` | List sites for estate |
| GET | `/api/sites/:id` | Get site by ID |
| POST | `/api/estates/:estateId/sites` | Create site |
| PATCH | `/api/sites/:id` | Update site |
| DELETE | `/api/sites/:id` | Delete site |

**GET /api/estates/:estateId/sites**

Query: `?page=1&limit=20`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "estate_id": "uuid",
      "name": "string",
      "site_type": "string",
      "address_line1": "string",
      "city": "string",
      "postcode": "string",
      "country": "string",
      "latitude": 0,
      "longitude": 0,
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/sites/:id**

Response (200):
```json
{
  "id": "uuid",
  "estate_id": "uuid",
  "name": "string",
  "site_type": "string",
  "address_line1": "string",
  "address_line2": "string",
  "city": "string",
  "postcode": "string",
  "country": "string",
  "latitude": 0,
  "longitude": 0,
  "operating_hours": "string",
  "occupancy_profile": "string",
  "public_access_level": "string",
  "vulnerable_occupants": "string",
  "critical_services": "string",
  "crime_intelligence": {
    "calculated_threat_score": 1,
    "total_crimes": 0,
    "data_month": "YYYY-MM",
    "fetched_at": "ISO8601"
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**POST /api/estates/:estateId/sites**

Request:
```json
{
  "name": "string",
  "site_type": "string",
  "address_line1": "string",
  "address_line2": "string",
  "city": "string",
  "postcode": "string",
  "country": "string",
  "latitude": 0,
  "longitude": 0,
  "operating_hours": "string",
  "occupancy_profile": "string",
  "public_access_level": "string",
  "vulnerable_occupants": "string",
  "critical_services": "string"
}
```

Response (201): Same shape as GET /api/sites/:id

**PATCH /api/sites/:id**

Request: Partial object

Response (200): Same shape as GET /api/sites/:id

**DELETE /api/sites/:id**

Response (204): No content

---

### Assessments CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sites/:siteId/assessments` | List assessments for site |
| GET | `/api/assessments/:id` | Get assessment by ID |
| POST | `/api/sites/:siteId/assessments` | Create assessment |
| PATCH | `/api/assessments/:id` | Update assessment |
| DELETE | `/api/assessments/:id` | Delete assessment |

**GET /api/sites/:siteId/assessments**

Query: `?page=1&limit=20&status=`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "site_id": "uuid",
      "template_id": "uuid",
      "assessor_id": "uuid",
      "status": "draft | in_progress | completed",
      "assessment_type": "string",
      "assessed_at": "YYYY-MM-DD | null",
      "completed_at": "ISO8601 | null",
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/assessments/:id**

Response (200):
```json
{
  "id": "uuid",
  "site_id": "uuid",
  "template_id": "uuid",
  "assessor_id": "uuid",
  "status": "string",
  "assessment_type": "string",
  "assessed_at": "YYYY-MM-DD | null",
  "completed_at": "ISO8601 | null",
  "responses": [{ "question_id": "uuid", "selected_score": 1, "comment": "string", "is_not_applicable": false }],
  "risk_scores": [{ "layer": "string", "score_value": 0, "band": "string" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**POST /api/sites/:siteId/assessments**

Request:
```json
{
  "template_id": "uuid",
  "assessment_type": "rapid | standard | enhanced | scenario"
}
```

Response (201): Same shape as GET /api/assessments/:id

**PATCH /api/assessments/:id**

Request: Partial object (e.g. `{ "status": "in_progress" }`, `{ "status": "completed" }`)

Response (200): Same shape as GET /api/assessments/:id

**DELETE /api/assessments/:id**

Response (204): No content

---

### Actions CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sites/:siteId/actions` | List actions for site |
| GET | `/api/actions/:id` | Get action by ID |
| POST | `/api/sites/:siteId/actions` | Create action |
| PATCH | `/api/actions/:id` | Update action |
| DELETE | `/api/actions/:id` | Delete action |

**GET /api/sites/:siteId/actions**

Query: `?page=1&limit=20&status=&priority=`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "site_id": "uuid",
      "assessment_id": "uuid | null",
      "title": "string",
      "description": "string",
      "priority": "string",
      "owner_id": "uuid | null",
      "due_date": "YYYY-MM-DD | null",
      "status": "open | in_progress | closed",
      "residual_risk_after_closure": 0,
      "created_at": "ISO8601",
      "updated_at": "ISO8601",
      "closed_at": "ISO8601 | null"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/actions/:id**

Response (200):
```json
{
  "id": "uuid",
  "site_id": "uuid",
  "assessment_id": "uuid | null",
  "title": "string",
  "description": "string",
  "priority": "string",
  "owner_id": "uuid | null",
  "due_date": "YYYY-MM-DD | null",
  "status": "string",
  "residual_risk_after_closure": 0,
  "updates": [{ "id": "uuid", "new_status": "string", "comment": "string", "created_at": "ISO8601" }],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "closed_at": "ISO8601 | null"
}
```

**POST /api/sites/:siteId/actions**

Request:
```json
{
  "assessment_id": "uuid | null",
  "title": "string",
  "description": "string",
  "priority": "string",
  "owner_id": "uuid | null",
  "due_date": "YYYY-MM-DD | null"
}
```

Response (201): Same shape as GET /api/actions/:id

**PATCH /api/actions/:id**

Request: Partial object (e.g. `{ "status": "in_progress" }`, `{ "status": "closed" }`)

Response (200): Same shape as GET /api/actions/:id

**DELETE /api/actions/:id**

Response (204): No content

---

### Reports Generation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sites/:siteId/reports` | List reports for site |
| GET | `/api/assessments/:assessmentId/reports` | List reports for assessment |
| GET | `/api/reports/:id` | Get report by ID |
| POST | `/api/reports/generate` | Generate new report |

**GET /api/sites/:siteId/reports**

Query: `?page=1&limit=20&report_type=`

Response (200):
```json
{
  "data": [
    {
      "id": "uuid",
      "site_id": "uuid",
      "assessment_id": "uuid | null",
      "report_type": "string",
      "title": "string",
      "file_url": "string | null",
      "generated_by_id": "uuid",
      "created_at": "ISO8601"
    }
  ],
  "meta": { "total": 0, "page": 1, "limit": 20 }
}
```

**GET /api/reports/:id**

Response (200):
```json
{
  "id": "uuid",
  "site_id": "uuid",
  "assessment_id": "uuid | null",
  "report_type": "assessment | summary | executive",
  "title": "string",
  "content": {},
  "file_url": "string | null",
  "generated_by_id": "uuid",
  "created_at": "ISO8601"
}
```

**POST /api/reports/generate**

Request:
```json
{
  "site_id": "uuid",
  "assessment_id": "uuid | null",
  "report_type": "assessment | summary | executive"
}
```

Response (201):
```json
{
  "id": "uuid",
  "report_type": "string",
  "title": "string",
  "file_url": "string | null",
  "status": "generating | ready",
  "created_at": "ISO8601"
}
```
