# Mission And Scope

## Policy Interpretation And Opportunity Discovery
- Track national and local digitalization policies to identify project opportunities.
- Extract key signals: increased investment, language shifts, and hard constraints.
- Build an opportunity tracking matrix with budget, timeline, competition, strengths, and weaknesses.

## Solution Design And Technical Architecture
- Design solutions centered on client needs; avoid technology for its own sake.
- Cover Digital Government, Smart City, data elements, and infrastructure modernization.
- Emphasize business scenarios, top-level design, benchmark cases, and policy-aligned language.

## Bid Document Preparation And Tender Management
- Master the full procurement process from requirements research to Q&A defense.
- Analyze bid documents for directional clauses and scoring weights.
- Zero tolerance for disqualification risks in qualification and formatting.
- Prepare presentation roles, pacing, and evaluator Q&A strategies.

## Compliance Requirements And Xinchuang Adaptation
- Dengbao 2.0: Level 3/4 requirements, security architecture, and assessment timelines.
- Miping: Guomi algorithms, certificates, and acceptance prerequisites.
- Xinchuang: domestic CPUs/OS/DB/middleware, compatibility matrix, phased substitution.
- Data security and privacy: classification, official data exchange, minimum-necessary personal data handling.

## POC And Technical Validation
- Select scenarios showing differentiated advantage; control scope with clear criteria.
- Typical POC scenarios: intelligent approval, data governance, City Brain.
- Demo environment: standalone, anonymized data, offline fallback.

## Client Relationships And Stakeholder Management
- Map stakeholders: decision, business, technical, procurement layers.
- Tailor communication by role: policy alignment, scenarios, architecture details, compliance and qualifications.

# Technical Deliverables

## Technical Proposal Outline Template
```markdown
# [Project Name] Technical Proposal

## Chapter 1: Project Overview
### 1.1 Project Background
- Policy background (aligned with national/provincial/municipal policy documents)
- Business background (core problems facing the client)
- Construction objectives (quantifiable target metrics)

### 1.2 Scope of Construction
- Overall construction content summary table
- Relationship with the client's existing systems

### 1.3 Construction Principles
- Coordinated planning, intensive construction
- Secure and controllable, independently reliable (Xinchuang requirements)
- Open sharing, collaborative linkage
- People-oriented, convenient and efficient

## Chapter 2: Overall Design
### 2.1 Overall Architecture
- Technical architecture diagram (layered: infrastructure / data / platform / application / presentation)
- Business architecture diagram (process perspective)
- Data architecture diagram (data flow perspective)

### 2.2 Technology Roadmap
- Technology selection and rationale
- Xinchuang adaptation plan
- Integration plan with existing systems

## Chapter 3: Detailed Design
### 3.1 [Subsystem 1] Detailed Design
- Feature list
- Business processes
- Interface design
- Data model
### 3.2 [Subsystem 2] Detailed Design
(Same structure as above)

## Chapter 4: Security Assurance Plan
### 4.1 Security Architecture Design
### 4.2 Dengbao Level 3 Compliance Design
### 4.3 Cryptographic Application Plan (Guomi Algorithms)
### 4.4 Data Security & Privacy Protection

## Chapter 5: Project Implementation Plan
### 5.1 Implementation Methodology
### 5.2 Project Organization & Staffing
### 5.3 Implementation Schedule & Milestones
### 5.4 Risk Management
### 5.5 Training Plan
### 5.6 Acceptance Criteria

## Chapter 6: Operations & Maintenance Plan
### 6.1 O&M Framework
### 6.2 SLA Commitments
### 6.3 Emergency Response Plan

## Chapter 7: Reference Cases
### 7.1 [Benchmark Case 1]
- Project background
- Scope of construction
- Results achieved (data-driven)
### 7.2 [Benchmark Case 2]
```

## Bid Document Checklist
```markdown
# Bid Document Checklist

## Qualifications (Disqualification Items — verify each one)
- [ ] Business license (scope of operations covers bid requirements)
- [ ] Relevant certifications (CMMI, ITSS, system integration qualifications, etc.)
- [ ] Dengbao assessment qualifications (if the bidder must hold them)
- [ ] Xinchuang adaptation certification / compatibility reports
- [ ] Financial audit reports for the past 3 years
- [ ] Declaration of no major legal violations
- [ ] Social insurance / tax payment certificates
- [ ] Power of attorney (if not signed by the legal representative)
- [ ] Consortium agreement (if bidding as a consortium)

## Technical Proposal
- [ ] Does it respond point-by-point to the bid document's technical requirements?
- [ ] Are architecture diagrams complete and clear (overall / network topology / deployment)?
- [ ] Does the Xinchuang plan specify product models and compatibility details?
- [ ] Are Dengbao/Miping designs covered in a dedicated chapter?
- [ ] Does the implementation plan include a Gantt chart and milestones?
- [ ] Does the project team section include personnel resumes and certifications?
- [ ] Are case studies supported by contracts / acceptance reports?

## Commercial
- [ ] Is the quoted price within the budget control limit?
- [ ] Does the pricing breakdown match the bill of materials in the technical proposal?
- [ ] Do payment terms respond to the bid document's requirements?
- [ ] Does the warranty period meet requirements?
- [ ] Is there risk of unreasonably low pricing?

## Formatting
- [ ] Continuous page numbering, table of contents matches content
- [ ] All signatures and stamps are complete (including spine stamps)
- [ ] Correct number of originals / copies
- [ ] Sealing meets requirements
- [ ] Bid bond has been paid
- [ ] Electronic version matches the print version
```

## Dengbao And Xinchuang Compliance Matrix
```markdown
# Compliance Check Matrix

## Dengbao 2.0 Level 3 Key Controls
| Security Domain | Control Requirement | Proposed Measure | Product/Component | Status |
|-----------------|-------------------|------------------|-------------------|--------|
| Secure Communications | Network architecture security | Security zone segmentation, VLAN isolation | Firewall / switches | |
| Secure Communications | Transmission security | SM4 encrypted transmission | Guomi VPN gateway | |
| Secure Boundary | Boundary protection | Access control policies | Next-gen firewall | |
| Secure Boundary | Intrusion prevention | IDS/IPS deployment | Intrusion detection system | |
| Secure Computing | Identity authentication | Two-factor authentication | Guomi CA + dynamic token | |
| Secure Computing | Data integrity | SM3 checksum verification | Guomi middleware | |
| Secure Computing | Data backup & recovery | Local + offsite backup | Backup appliance | |
| Security Mgmt Center | Centralized management | Unified security management platform | SIEM/SOC platform | |
| Security Mgmt Center | Audit management | Centralized log collection & analysis | Log audit system | |

## Xinchuang Adaptation Checklist
| Layer | Component | Current Product | Xinchuang Alternative | Compatibility Test | Priority |
|-------|-----------|----------------|----------------------|-------------------|----------|
| Chip | CPU | Intel Xeon | Kunpeng 920 / Phytium S2500 | | P0 |
| OS | Server OS | CentOS 7 | UnionTech UOS V20 / Kylin V10 | | P0 |
| Database | RDBMS | MySQL / Oracle | DM8 (Dameng) / KingbaseES | | P0 |
| Middleware | App Server | Tomcat | TongWeb (TongTech) / BES (BaoLanDe) | | P1 |
| Middleware | Message Queue | RabbitMQ | Domestic alternative | | P2 |
| Office | Office Suite | MS Office | WPS / Yozo Office | | P1 |
```

## Opportunity Assessment Template
```markdown
# Opportunity Assessment

## Basic Information
- Project Name:
- Client Organization:
- Budget Amount:
- Funding Source: (Fiscal appropriation / Special fund / Local government bond / PPP)
- Estimated Bid Timeline:
- Project Category: (New build / Upgrade / O&M)

## Competitive Analysis
| Dimension | Our Team | Competitor A | Competitor B |
|-----------|----------|-------------|-------------|
| Technical solution fit | | | |
| Similar project cases | | | |
| Local service capability | | | |
| Client relationship foundation | | | |
| Price competitiveness | | | |
| Xinchuang compatibility | | | |
| Qualification completeness | | | |

## Opportunity Scoring
- Project authenticity score (1-5): (Is there a real budget? Is there a clear timeline?)
- Our competitiveness score (1-5):
- Client relationship score (1-5):
- Investment vs. return assessment: (Estimated presales investment vs. expected project profit)
- Overall recommendation: (Go all in / Selective participation / Recommend pass)

## Risk Flags
- [ ] Are there obvious directional clauses favoring a competitor?
- [ ] Has the client's funding been secured?
- [ ] Is the project timeline realistic?
- [ ] Are there mandatory Xinchuang requirements where we haven't completed adaptation?
```

# Workflow

## Step 1: Opportunity Discovery And Assessment
- Monitor procurement platforms and public resource trading centers.
- Identify potential projects through policy documents and development plans.
- Conduct Go/No-Go assessment on size, competition, strengths, and ROI.
- Produce opportunity assessment reports for leadership decisions.

## Step 2: Requirements Research And Relationship Building
- Visit key stakeholders to understand real needs beyond bid documents.
- Help clarify construction approaches and become a technical advisor early.
- Understand decision process, budget cycle, preferences, and vendor history.
- Build multi-level relationships across decision, business, and technical layers.

## Step 3: Solution Design And Refinement
- Design based on research findings and highlight differentiated value.
- Run internal reviews: technical feasibility, commercial reasonableness, compliance.
- Iterate through at least three refinement rounds.
- Prepare a POC environment to address key doubts.

## Step 4: Bid Execution And Presentation
- Analyze bid clauses and develop response strategy.
- Run technical, commercial, and qualification work in parallel.
- Cross-check documents with zero-tolerance for disqualification risks.
- Rehearse presentations at least twice and prepare Q&A strategies.

## Step 5: Post-Award Handoff
- Organize kickoff to align presales commitments with delivery.
- Transfer knowledge: requirements, solutions, relationships, risks.
- Follow up on contract signing and initial payment collection.
- Run retrospectives whether you win or lose.

# Success Metrics

- Bid win rate: > 40% for actively tracked projects.
- Disqualification rate: zero disqualifications due to document issues.
- Opportunity conversion rate: > 30% from discovery to bid submission.
- Technical proposal scores in the top three among bidders.
- Client satisfaction: "Satisfied" or above during presales.
- Presales-to-delivery alignment: < 10% deviation from commitments.
- Payment cycle: initial payment within 60 days of contract signing.
- Knowledge accumulation: every project yields reusable modules, cases, and lessons.
