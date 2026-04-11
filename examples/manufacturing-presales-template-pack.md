# Manufacturing Presales Template Pack

A practical template pack for non-standard automation equipment and production-line projects, especially automotive electronics and home appliance manufacturing scenarios.

## What This Includes

This pack gives manufacturing teams reusable scaffolding to run early discovery, presales qualification, quotation gating, and cross-functional reviews with the Manufacturing Division agents.

### Recommended agent pairing

| Task | Best-fit agent |
|---|---|
| Customer discovery and scope framing | Non-Standard Automation Sales Engineer |
| Concept architecture and station breakdown | Automation Solutions Architect |
| Validation coverage and acceptance logic | Test and Validation Engineer |
| Process conversion from manual to automated | Process Industrialization Engineer |
| Complaint containment and recurrence prevention | Quality and 8D Engineer |
| Launch coordination and milestone control | Program Launch Manager |
| PLC/debug/startup recovery | Controls and Commissioning Engineer |
| Long-lead and supplier follow-up | Sourcing and Supplier Coordination Manager |
| Field issue recovery and service knowledge capture | After-Sales Service Engineer |
| Ramp stabilization and micro-stop reduction | Production Ramp Optimizer |

---

## Base templates

### 1. Sales solution prompt

Use this prompt with customer emails, meeting notes, line photos, or requirement fragments.

```text
You are a non-standard automation solutions sales engineer serving automotive electronics and home appliance manufacturers.

Your job is to help the sales and project team quickly produce:
1. customer requirement summary
2. preliminary solution understanding
3. open questions
4. risks
5. recommended next actions
6. quotation-precheck field list

Output principles:
- Be practical, not generic.
- Prioritize scope boundaries, takt time, yield, labor replacement, interfaces, and acceptance criteria.
- If information is incomplete, explicitly list open questions instead of inventing details.
- Flag cost-sensitive and high-risk items before quotation.

Use this output structure:

## 1. Customer requirement summary
- Industry:
- Product:
- Project type: standalone machine / station / linked cell / line retrofit / new line
- Core target: efficiency / cost down / yield / labor replacement / traceability / flexibility / other
- Current pain points:

## 2. Preliminary solution understanding
Cover:
- process understanding
- machine or line scope
- upstream and downstream interfaces
- required automation units
- key control points
- inspection and traceability needs
- likely PLC / robot / vision / MES / barcode / RFID / test-system involvement

## 3. Open questions
At minimum cover:
- product and process parameters
- takt and throughput targets
- uptime and yield targets
- site and utility conditions
- infeed / outfeed method
- staffing model
- quality requirements
- acceptance criteria
- schedule milestones
- budget and purchasing mode

## 4. Risks
Assess at minimum:
- technical risk
- process maturity risk
- takt achievement risk
- yield risk
- supply-chain / long-lead risk
- customer change risk
- site-condition risk
- interface / integration risk
- unclear acceptance-definition risk

## 5. Recommended next actions
Prioritize actions such as:
- collect missing data
- schedule site survey
- run takt estimation
- hold technical clarification meeting
- request sample validation
- run internal risk review
- split phase 1 / phase 2 scope
- decide whether quotation should proceed

## 6. Quotation precheck field list
Provide a structured field list that can be copied into a table.

Customer information:
[Paste customer requirement, email thread, meeting notes, or drawings here]
```

### 2. Customer requirement intake form

```text
Customer name:
Industry:
Factory location:
Department involved:
Primary contact:
Project code:

Project background:
- new product introduction / retrofit / capacity expansion / cost-down / quality improvement / labor replacement / other
- current production mode:
- current major pain points:
- target metrics to improve:

Product and process:
- product name:
- model count:
- mixed-model line required:
- size / weight range:
- process flow:
- special process requirements:
- CTQ / critical quality points:
- sample available:
- drawing / 3D / process document available:

Capacity and takt:
- annual volume:
- monthly volume:
- shift model:
- UPH target:
- takt target:
- OEE target:
- yield target:

Automation scope:
- standalone / station / small line / full line
- robot needed:
- vision needed:
- test equipment needed:
- traceability needed:
- MES / ERP integration needed:
- PLC / HMI preferences:
- remote support needed:

Site conditions:
- footprint limit:
- height limit:
- floor loading:
- power:
- air:
- network:
- temperature / humidity / cleanliness:
- EHS / ESD / explosion-proof constraints:

Acceptance and commercial:
- acceptance metrics:
- launch target date:
- RFQ deadline:
- budget range:
- procurement mode:
- competing vendors involved:

Next steps:
- missing materials from customer:
- site survey needed:
- technical review meeting needed:
- sample test needed:
- quotation ready: yes / no
```

### 3. Quotation precheck form

```text
Project basics:
- customer:
- project:
- sales owner:
- solution owner:
- quote version:
- quote date:

Demand clarity:
- written requirement exists: yes / no
- drawings / samples / takt / acceptance data complete: yes / no
- unresolved critical points:

Scope:
- included scope:
- excluded scope:
- customer-supplied items:
- third-party supplied items:
- installation included: yes / no
- commissioning included: yes / no
- training included: yes / no
- acceptance support included: yes / no

Technical feasibility:
- technically feasible: yes / no
- similar project reference exists: yes / no
- takt estimated: yes / no
- yield feasibility assessed: yes / no
- main technical challenges:
- out-of-capability items:

Cost:
- mechanical cost assessed: yes / no
- electrical cost assessed: yes / no
- vision / test cost assessed: yes / no
- purchased and outsourced parts assessed: yes / no
- software effort assessed: yes / no
- travel / install / debug cost assessed: yes / no
- risk reserve included: yes / no

Supply chain and site:
- long-lead items identified: yes / no
- customer-specified brands: yes / no
- import risk: yes / no
- site utilities confirmed: yes / no
- installation path confirmed: yes / no

Acceptance and payment:
- acceptance criteria clear: yes / no
- pre-FAT / SAT conditions:
- warranty period:
- payment milestones:
- risky payment terms:

Conclusion:
- quotation allowed: yes / conditional / no
- quotation strategy: standard / conservative / risk-loaded / phased
- major risk notes:
```

### 4. Visit memo template

```text
Customer:
Visit date:
Location:
Our attendees:
Customer attendees:
Project:
Memo owner:

Visit purpose:
- discovery / site survey / solution review / technical clarification / commercial discussion / service issue / other
- objective:

Current state:
- current line or machine status:
- current labor setup:
- current capacity and takt:
- biggest current problems:
- metrics customer cares about most:

Customer asks:
1.
2.
3.

Site observations:
- process flow:
- bottleneck station:
- quality risks:
- logistics / handling issues:
- safety / space constraints:
- line or IT interface situation:
- other findings:

Confirmed items:
- 
- 
- 

Open items:
- waiting on customer:
- waiting on internal review:
- waiting on second site check:

Risk judgment:
- technical risk:
- delivery risk:
- supply risk:
- change risk:
- acceptance risk:

Next actions:
- our actions:
- customer actions:
- owners:
- due date:
- next meeting date:
```

---

## Table-field versions

Use these when converting the pack into CRM, ERP, Excel, Feishu multi-dimensional tables, or internal approval forms.

### Core field groups

- customer basics
- project basics
- product and process details
- takt / capacity / yield targets
- automation scope
- site constraints and utilities
- integration requirements
- acceptance metrics
- commercial conditions
- supply-chain risks
- next-step ownership

Recommended statuses:
- lead captured
- waiting for info
- solution drafting
- pending internal review
- quotation ready
- quotation blocked
- on hold

---

## Advanced templates

### 5. Technical agreement confirmation sheet
Use before final quotation freeze, design freeze, or FAT alignment.

Include:
- supply scope and exclusions
- process and product assumptions
- takt, yield, uptime, and changeover targets
- station composition
- PLC / HMI / robot / vision / test module requirements
- upstream/downstream and MES interfaces
- utility and safety requirements
- FAT / SAT acceptance criteria
- delivery schedule and service commitments
- change-control rules

### 6. Project risk register
Track at least:
- demand change risk
- process maturity risk
- takt risk
- yield risk
- long-lead risk
- outsourced fabrication risk
- site readiness risk
- interface risk
- acceptance ambiguity risk
- payment risk
- service recurrence risk
- internal coordination risk

Recommended columns:
- risk category
- description
- trigger
- impact
- severity
- prevention action
- contingency plan
- owner
- status

### 7. Presales site survey form
Use on-site before concept freeze.

Capture:
- current process and line layout
- bottleneck stations and abnormality patterns
- incoming / outgoing logistics method
- utility conditions
- floor-space constraints
- IT / MES / barcode / RFID reality on site
- current quality pain points
- customer targets, timing, and budget
- whether automation introduction is actually justified

### 8. Solution review sheet
Use for internal cross-functional review.

Review dimensions:
- requirement completeness
- technical feasibility
- cost and sourcing realism
- delivery and commissioning feasibility
- acceptance and after-sales readiness
- final decision: pass / conditional pass / fail
- action list with owner and due date

---

## Suggested workflow

1. Capture customer information with the intake form.
2. Run the Sales Engineer agent to structure the opportunity.
3. Pull in the Solutions Architect for concept shaping.
4. Use the Quotation Precheck before any price release.
5. Run the Solution Review Sheet with mechanical, electrical, software, sourcing, PM, and service.
6. Freeze key assumptions in the Technical Agreement Confirmation Sheet.
7. Track risks with the Project Risk Register through launch and ramp.

## Why this matters

These templates make the Manufacturing Division more actionable in real delivery scenarios. Instead of only defining personas, they show how the agents can support day-to-day factory sales, quotation gating, launch control, commissioning, and ramp stabilization work.