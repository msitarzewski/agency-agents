# NEXUS — Phase Details (0–6)

> Phase-by-phase agent roster, workstreams, and quality gates. Summary and pipeline overview: see the strategy overview.

[← Back to the NEXUS strategy overview](nexus-strategy.md)


---

## 3. Phase 0 — Intelligence & Discovery

> **Objective**: Understand the landscape before committing resources. No building until the problem is validated.

### 3.1 Active Agents

| Agent | Role in Phase | Primary Output |
|-------|--------------|----------------|
| **Trend Researcher** | Market intelligence lead | Market Analysis Report with TAM/SAM/SOM |
| **Feedback Synthesizer** | User needs analysis | Synthesized Feedback Report with pain points |
| **UX Researcher** | User behavior analysis | Research Findings with personas and journey maps |
| **Analytics Reporter** | Data landscape assessment | Data Audit Report with available signals |
| **Legal Compliance Checker** | Regulatory scan | Compliance Requirements Matrix |
| **Tool Evaluator** | Technology landscape | Tech Stack Assessment |

### 3.2 Parallel Workstreams

```
WORKSTREAM A: Market Intelligence          WORKSTREAM B: User Intelligence
├── Trend Researcher                       ├── Feedback Synthesizer
│   ├── Competitive landscape              │   ├── Multi-channel feedback collection
│   ├── Market sizing (TAM/SAM/SOM)        │   ├── Sentiment analysis
│   └── Trend lifecycle mapping            │   └── Pain point prioritization
│                                          │
├── Analytics Reporter                     ├── UX Researcher
│   ├── Existing data audit                │   ├── User interviews/surveys
│   ├── Signal identification              │   ├── Persona development
│   └── Baseline metrics                   │   └── Journey mapping
│                                          │
└── Legal Compliance Checker               └── Tool Evaluator
    ├── Regulatory requirements                ├── Technology assessment
    ├── Data handling constraints               ├── Build vs. buy analysis
    └── Jurisdiction mapping                   └── Integration feasibility
```

### 3.3 Phase 0 Quality Gate

**Gate Keeper**: Executive Summary Generator

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Market opportunity validated | TAM > minimum viable threshold | Trend Researcher report with sources |
| User need confirmed | ≥3 validated pain points | Feedback Synthesizer + UX Researcher data |
| Regulatory path clear | No blocking compliance issues | Legal Compliance Checker matrix |
| Data foundation assessed | Key metrics identified | Analytics Reporter audit |
| Technology feasibility confirmed | Stack validated | Tool Evaluator assessment |

**Output**: Executive Summary (≤500 words, SCQA format) → Decision: GO / NO-GO / PIVOT

---

## 4. Phase 1 — Strategy & Architecture

> **Objective**: Define what we're building, how it's structured, and what success looks like — before writing a single line of code.

### 4.1 Active Agents

| Agent | Role in Phase | Primary Output |
|-------|--------------|----------------|
| **Studio Producer** | Strategic portfolio alignment | Strategic Portfolio Plan |
| **Senior Project Manager** | Spec-to-task conversion | Comprehensive Task List |
| **Sprint Prioritizer** | Feature prioritization | Prioritized Backlog (RICE scored) |
| **UX Architect** | Technical architecture + UX foundation | Architecture Spec + CSS Design System |
| **Brand Guardian** | Brand identity system | Brand Foundation Document |
| **Backend Architect** | System architecture | System Architecture Specification |
| **AI Engineer** | AI/ML architecture (if applicable) | ML System Design |
| **Finance Tracker** | Budget and resource planning | Financial Plan with ROI projections |

### 4.2 Execution Sequence

```
STEP 1: Strategic Framing (Parallel)
├── Studio Producer → Strategic Portfolio Plan (vision, objectives, ROI targets)
├── Brand Guardian → Brand Foundation (purpose, values, visual identity system)
└── Finance Tracker → Budget Framework (resource allocation, cost projections)

STEP 2: Technical Architecture (Parallel, after Step 1)
├── UX Architect → CSS Design System + Layout Framework + UX Structure
├── Backend Architect → System Architecture (services, databases, APIs)
├── AI Engineer → ML Architecture (models, pipelines, inference strategy)
└── Senior Project Manager → Task List (spec → tasks, exact requirements)

STEP 3: Prioritization (Sequential, after Step 2)
└── Sprint Prioritizer → RICE-scored backlog with sprint assignments
    ├── Input: Task List + Architecture Spec + Budget Framework
    ├── Output: Prioritized sprint plan with dependency map
    └── Validation: Studio Producer confirms strategic alignment
```

### 4.3 Phase 1 Quality Gate

**Gate Keeper**: Studio Producer + Reality Checker (dual sign-off)

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Architecture covers all requirements | 100% spec coverage | Senior PM task list cross-referenced |
| Brand system complete | Logo, colors, typography, voice defined | Brand Guardian deliverable |
| Technical feasibility validated | All components have implementation path | Backend Architect + UX Architect specs |
| Budget approved | Within organizational constraints | Finance Tracker plan |
| Sprint plan realistic | Velocity-based estimation | Sprint Prioritizer backlog |

**Output**: Approved Architecture Package → Phase 2 activation

---

## 5. Phase 2 — Foundation & Scaffolding

> **Objective**: Build the technical and operational foundation that all subsequent work depends on. Get the skeleton standing before adding muscle.

### 5.1 Active Agents

| Agent | Role in Phase | Primary Output |
|-------|--------------|----------------|
| **DevOps Automator** | CI/CD pipeline + infrastructure | Deployment Pipeline + IaC Templates |
| **Frontend Developer** | Project scaffolding + component library | App Skeleton + Design System Implementation |
| **Backend Architect** | Database + API foundation | Schema + API Scaffold + Auth System |
| **UX Architect** | CSS system implementation | Design Tokens + Layout Framework |
| **Infrastructure Maintainer** | Cloud infrastructure setup | Monitoring + Logging + Alerting |
| **Studio Operations** | Process setup | Collaboration tools + workflows |

### 5.2 Parallel Workstreams

```
WORKSTREAM A: Infrastructure              WORKSTREAM B: Application Foundation
├── DevOps Automator                      ├── Frontend Developer
│   ├── CI/CD pipeline (GitHub Actions)   │   ├── Project scaffolding
│   ├── Container orchestration           │   ├── Component library setup
│   └── Environment provisioning          │   └── Design system integration
│                                         │
├── Infrastructure Maintainer             ├── Backend Architect
│   ├── Cloud resource provisioning       │   ├── Database schema deployment
│   ├── Monitoring (Prometheus/Grafana)   │   ├── API scaffold + auth
│   └── Security hardening               │   └── Service communication layer
│                                         │
└── Studio Operations                     └── UX Architect
    ├── Git workflow + branch strategy        ├── CSS design tokens
    ├── Communication channels                ├── Responsive layout system
    └── Documentation templates               └── Theme system (light/dark/system)
```

### 5.3 Phase 2 Quality Gate

**Gate Keeper**: DevOps Automator + Evidence Collector

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| CI/CD pipeline operational | Build + test + deploy working | Pipeline execution logs |
| Database schema deployed | All tables/indexes created | Migration success + schema dump |
| API scaffold responding | Health check endpoints live | curl response screenshots |
| Frontend rendering | Skeleton app loads in browser | Evidence Collector screenshots |
| Monitoring active | Dashboards showing metrics | Grafana/monitoring screenshots |
| Design system implemented | Tokens + components available | Component library demo |

**Output**: Working skeleton application with full DevOps pipeline → Phase 3 activation

---

## 6. Phase 3 — Build & Iterate

> **Objective**: Implement features through continuous Dev↔QA loops. Every task is validated before the next begins. This is where the bulk of the work happens.

### 6.1 The Dev↔QA Loop

This is the heart of NEXUS. The Agents Orchestrator manages a **task-by-task quality loop**:

```
┌─────────────────────────────────────────────────────────┐
│                   DEV ↔ QA LOOP                          │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ Developer │───▶│ Evidence │───▶│ Decision Logic    │   │
│  │ Agent     │    │ Collector│    │                   │   │
│  │           │    │ (QA)     │    │ PASS → Next Task  │   │
│  │ Implements│    │          │    │ FAIL → Retry (≤3) │   │
│  │ Task N    │    │ Tests    │    │ BLOCKED → Escalate│   │
│  │           │◀───│ Task N   │◀───│                   │   │
│  └──────────┘    └──────────┘    └──────────────────┘   │
│       ▲                                    │             │
│       │            QA Feedback             │             │
│       └────────────────────────────────────┘             │
│                                                          │
│  Orchestrator tracks: attempt count, QA feedback,        │
│  task status, cumulative quality metrics                 │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Agent Assignment by Task Type

| Task Type | Primary Developer | QA Agent | Specialist Support |
|-----------|------------------|----------|-------------------|
| Frontend UI | Frontend Developer | Evidence Collector | UI Designer, Whimsy Injector |
| Backend API | Backend Architect | API Tester | Performance Benchmarker |
| Database | Backend Architect | API Tester | Analytics Reporter |
| Mobile | Mobile App Builder | Evidence Collector | UX Researcher |
| AI/ML Feature | AI Engineer | Test Results Analyzer | Analytics Reporter |
| Infrastructure | DevOps Automator | Performance Benchmarker | Infrastructure Maintainer |
| Premium Polish | Senior Developer | Evidence Collector | Visual Storyteller |
| Rapid Prototype | Rapid Prototyper | Evidence Collector | Experiment Tracker |
| Spatial/XR | XR Immersive Developer | Evidence Collector | XR Interface Architect |
| visionOS | visionOS Spatial Engineer | Evidence Collector | macOS Spatial/Metal Engineer |
| Cockpit UI | XR Cockpit Interaction Specialist | Evidence Collector | XR Interface Architect |
| CLI/Terminal | Terminal Integration Specialist | API Tester | LSP/Index Engineer |
| Code Intelligence | LSP/Index Engineer | Test Results Analyzer | Senior Developer |

### 6.3 Parallel Build Tracks

For complex projects, multiple tracks run simultaneously:

```
TRACK A: Core Product                    TRACK B: Growth & Marketing
├── Frontend Developer                   ├── Growth Hacker
│   └── UI implementation                │   └── Viral loops + referral system
├── Backend Architect                    ├── Content Creator
│   └── API + business logic             │   └── Launch content + editorial calendar
├── AI Engineer                          ├── Social Media Strategist
│   └── ML features + pipelines          │   └── Cross-platform campaign
│                                        ├── App Store Optimizer (if mobile)
│                                        │   └── ASO strategy + metadata
│                                        │
TRACK C: Quality & Operations            TRACK D: Brand & Experience
├── Evidence Collector                   ├── UI Designer
│   └── Continuous QA screenshots        │   └── Component refinement
├── API Tester                           ├── Brand Guardian
│   └── Endpoint validation              │   └── Brand consistency audit
├── Performance Benchmarker              ├── Visual Storyteller
│   └── Load testing + optimization      │   └── Visual narrative assets
├── Workflow Optimizer                   └── Whimsy Injector
│   └── Process improvement                  └── Delight moments + micro-interactions
└── Experiment Tracker
    └── A/B test management
```

### 6.4 Phase 3 Quality Gate

**Gate Keeper**: Agents Orchestrator

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| All tasks pass QA | 100% task completion | Evidence Collector screenshots per task |
| API endpoints validated | All endpoints tested | API Tester report |
| Performance baselines met | P95 < 200ms, LCP < 2.5s | Performance Benchmarker report |
| Brand consistency verified | 95%+ adherence | Brand Guardian audit |
| No critical bugs | Zero P0/P1 open issues | Test Results Analyzer summary |

**Output**: Feature-complete application → Phase 4 activation

---

## 7. Phase 4 — Quality & Hardening

> **Objective**: The final quality gauntlet. The Reality Checker defaults to "NEEDS WORK" — you must prove production readiness with overwhelming evidence.

### 7.1 Active Agents

| Agent | Role in Phase | Primary Output |
|-------|--------------|----------------|
| **Reality Checker** | Final integration testing (defaults to NEEDS WORK) | Reality-Based Integration Report |
| **Evidence Collector** | Comprehensive visual evidence | Screenshot Evidence Package |
| **Performance Benchmarker** | Load testing + optimization | Performance Certification |
| **API Tester** | Full API regression suite | API Test Report |
| **Test Results Analyzer** | Aggregate quality metrics | Quality Metrics Dashboard |
| **Legal Compliance Checker** | Final compliance audit | Compliance Certification |
| **Infrastructure Maintainer** | Production readiness check | Infrastructure Readiness Report |
| **Workflow Optimizer** | Process efficiency review | Optimization Recommendations |

### 7.2 The Hardening Sequence

```
STEP 1: Evidence Collection (Parallel)
├── Evidence Collector → Full screenshot suite (desktop, tablet, mobile)
├── API Tester → Complete endpoint regression
├── Performance Benchmarker → Load test at 10x expected traffic
└── Legal Compliance Checker → Final regulatory audit

STEP 2: Analysis (Parallel, after Step 1)
├── Test Results Analyzer → Aggregate all test data into quality dashboard
├── Workflow Optimizer → Identify remaining process inefficiencies
└── Infrastructure Maintainer → Production environment validation

STEP 3: Final Judgment (Sequential, after Step 2)
└── Reality Checker → Integration Report
    ├── Cross-validates ALL previous QA findings
    ├── Tests complete user journeys with screenshot evidence
    ├── Verifies specification compliance point-by-point
    ├── Default verdict: NEEDS WORK
    └── READY only with overwhelming evidence across all criteria
```

### 7.3 Phase 4 Quality Gate (THE FINAL GATE)

**Gate Keeper**: Reality Checker (sole authority)

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| User journeys complete | All critical paths working | End-to-end screenshots |
| Cross-device consistency | Desktop + Tablet + Mobile | Responsive screenshots |
| Performance certified | P95 < 200ms, uptime > 99.9% | Load test results |
| Security validated | Zero critical vulnerabilities | Security scan report |
| Compliance certified | All regulatory requirements met | Legal Compliance Checker report |
| Specification compliance | 100% of spec requirements | Point-by-point verification |

**Verdict Options**:
- **READY** — Proceed to launch (rare on first pass)
- **NEEDS WORK** — Return to Phase 3 with specific fix list (expected)
- **NOT READY** — Major architectural issues, return to Phase 1/2

**Expected**: First implementations typically require 2-3 revision cycles. A B/B+ rating is normal and healthy.

---

## 8. Phase 5 — Launch & Growth

> **Objective**: Coordinate the go-to-market execution across all channels simultaneously. Maximum impact at launch.

### 8.1 Active Agents

| Agent | Role in Phase | Primary Output |
|-------|--------------|----------------|
| **Growth Hacker** | Launch strategy lead | Growth Playbook with viral loops |
| **Content Creator** | Launch content | Blog posts, videos, social content |
| **Social Media Strategist** | Cross-platform campaign | Campaign Calendar + Content |
| **Twitter Engager** | Twitter/X launch campaign | Thread strategy + engagement plan |
| **TikTok Strategist** | TikTok viral content | Short-form video strategy |
| **Instagram Curator** | Visual launch campaign | Visual content + stories |
| **Reddit Community Builder** | Authentic community launch | Community engagement plan |
| **App Store Optimizer** | Store optimization (if mobile) | ASO Package |
| **Executive Summary Generator** | Stakeholder communication | Launch Executive Summary |
| **Project Shepherd** | Launch coordination | Launch Checklist + Timeline |
| **DevOps Automator** | Deployment execution | Zero-downtime deployment |
| **Infrastructure Maintainer** | Launch monitoring | Real-time dashboards |

### 8.2 Launch Sequence

```
T-7 DAYS: Pre-Launch
├── Content Creator → Launch content queued and scheduled
├── Social Media Strategist → Campaign assets finalized
├── Growth Hacker → Viral mechanics tested and armed
├── App Store Optimizer → Store listing optimized
├── DevOps Automator → Blue-green deployment prepared
└── Infrastructure Maintainer → Auto-scaling configured for 10x

T-0: Launch Day
├── DevOps Automator → Execute deployment
├── Infrastructure Maintainer → Monitor all systems
├── Twitter Engager → Launch thread + real-time engagement
├── Reddit Community Builder → Authentic community posts
├── Instagram Curator → Visual launch content
├── TikTok Strategist → Launch videos published
├── Support Responder → Customer support active
└── Analytics Reporter → Real-time metrics dashboard

T+1 TO T+7: Post-Launch
├── Growth Hacker → Analyze acquisition data, optimize funnels
├── Feedback Synthesizer → Collect and analyze early user feedback
├── Analytics Reporter → Daily metrics reports
├── Content Creator → Response content based on reception
├── Experiment Tracker → Launch A/B tests
└── Executive Summary Generator → Daily stakeholder briefings
```

### 8.3 Phase 5 Quality Gate

**Gate Keeper**: Studio Producer + Analytics Reporter

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Deployment successful | Zero-downtime, all health checks pass | DevOps deployment logs |
| Systems stable | No P0/P1 incidents in first 48 hours | Infrastructure monitoring |
| User acquisition active | Channels driving traffic | Analytics Reporter dashboard |
| Feedback loop operational | User feedback being collected | Feedback Synthesizer report |
| Stakeholders informed | Executive summary delivered | Executive Summary Generator output |

**Output**: Stable launched product with active growth channels → Phase 6 activation

---

## 9. Phase 6 — Operate & Evolve

> **Objective**: Sustained operations with continuous improvement. The product is live — now make it thrive.

### 9.1 Active Agents (Ongoing)

| Agent | Cadence | Responsibility |
|-------|---------|---------------|
| **Infrastructure Maintainer** | Continuous | System reliability, uptime, performance |
| **Support Responder** | Continuous | Customer support and issue resolution |
| **Analytics Reporter** | Weekly | KPI tracking, dashboards, insights |
| **Feedback Synthesizer** | Bi-weekly | User feedback analysis and synthesis |
| **Finance Tracker** | Monthly | Financial performance, budget tracking |
| **Legal Compliance Checker** | Monthly | Regulatory monitoring and compliance |
| **Trend Researcher** | Monthly | Market intelligence and competitive analysis |
| **Executive Summary Generator** | Monthly | C-suite reporting |
| **Sprint Prioritizer** | Per sprint | Backlog grooming and sprint planning |
| **Experiment Tracker** | Per experiment | A/B test management and analysis |
| **Growth Hacker** | Ongoing | Acquisition optimization and growth experiments |
| **Workflow Optimizer** | Quarterly | Process improvement and efficiency gains |

### 9.2 Continuous Improvement Cycle

```
┌──────────────────────────────────────────────────────────┐
│              CONTINUOUS IMPROVEMENT LOOP                   │
│                                                           │
│  MEASURE          ANALYZE           PLAN          ACT     │
│  ┌─────────┐     ┌──────────┐     ┌─────────┐   ┌─────┐ │
│  │Analytics │────▶│Feedback  │────▶│Sprint   │──▶│Build│ │
│  │Reporter  │     │Synthesizer│    │Prioritizer│  │Loop │ │
│  └─────────┘     └──────────┘     └─────────┘   └─────┘ │
│       ▲                                            │      │
│       │              Experiment                    │      │
│       │              Tracker                       │      │
│       └────────────────────────────────────────────┘      │
│                                                           │
│  Monthly: Executive Summary Generator → C-suite report    │
│  Monthly: Finance Tracker → Financial performance         │
│  Monthly: Legal Compliance Checker → Regulatory update    │
│  Monthly: Trend Researcher → Market intelligence          │
│  Quarterly: Workflow Optimizer → Process improvements     │
└──────────────────────────────────────────────────────────┘
```
