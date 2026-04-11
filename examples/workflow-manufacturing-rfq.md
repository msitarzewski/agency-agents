# Multi-Agent Workflow: Manufacturing RFQ to Launch Readiness

> A step-by-step example of how to coordinate the Manufacturing Division agents for a real non-standard automation opportunity.

## The Scenario

A customer in automotive electronics wants a semi-automatic/manual assembly process upgraded into an automated line.

Customer ask (initially vague):
- Product: controller module assembly
- Goal: reduce labor, improve consistency, add traceability
- Timeline: pilot line in 10 weeks
- Current pain points: unstable output, operator variation, missed defects, rework during launch
- Unknowns: real takt definition, mixed-model scope, MES depth, acceptance threshold, incoming-material format

## Agent Team

| Agent | Role in this workflow |
|-------|------------------------|
| Non-Standard Automation Sales Engineer | Clarify the commercial and technical ask, separate facts from assumptions |
| Automation Solutions Architect | Turn requirements into line concept, station scope, and interface structure |
| Test and Validation Engineer | Define test coverage, golden sample logic, FAT/SAT evidence, and acceptance criteria |
| Process Industrialization Engineer | Convert manual process steps into stable, scalable automation logic |
| Quality and 8D Engineer | Surface launch risks, defect escape paths, and containment logic |
| Program Launch Manager | Sequence milestones, owners, and readiness gates |
| Controls and Commissioning Engineer | Stress-test startup, alarm handling, sequence logic, and debug realism |
| Sourcing and Supplier Coordination Manager | Identify long-lead materials, outsourced fabrication risks, and supplier blockers |
| After-Sales Service Engineer | Pre-think serviceability, field recovery, and issue knowledge capture |
| Production Ramp Optimizer | Plan post-SAT stabilization, micro-stop analysis, and output recovery |

## The Workflow

### Phase 1: RFQ Intake and Requirement Clarification

**Step 1 — Activate Non-Standard Automation Sales Engineer**

```text
Activate Non-Standard Automation Sales Engineer.

Customer: automotive electronics manufacturer
Project: controller module assembly automation line
Goal: reduce labor, improve consistency, add traceability
Target timing: pilot line in 10 weeks
Known pain points: unstable output, operator variation, missed defects, launch rework
Unknowns: takt definition, model mix, MES depth, incoming material format, acceptance threshold

Deliver:
1. customer requirement summary
2. preliminary solution understanding
3. must-confirm items
4. top quotation risks
5. next recommended actions
6. a quotation-readiness judgment
```

**Expected output:**
- a structured qualification brief
- a clarification-question set
- an assumption block that can be shared internally before quoting

### Phase 2: Parallel Concept Shaping

**Step 2 — Activate Automation Solutions Architect**

```text
Activate Automation Solutions Architect.

Here is the clarified requirement package: [paste Sales Engineer output]

Build a first-pass concept for the automation line.
Deliver:
1. likely station breakdown
2. process boundaries
3. manual vs automated split
4. upstream and downstream interfaces
5. key technical decisions and assumptions
6. open items that block concept freeze
```

**Step 3 — Activate Process Industrialization Engineer (in parallel)**

```text
Activate Process Industrialization Engineer.

Here is the clarified requirement package: [paste Sales Engineer output]

Translate the current manual process into an industrialization plan.
Deliver:
1. process-step breakdown
2. bottleneck assessment
3. operations suitable for automation
4. changeover and mixed-model concerns
5. process risks that could break takt or yield
```

**Step 4 — Activate Sourcing and Supplier Coordination Manager (in parallel)**

```text
Activate Sourcing and Supplier Coordination Manager.

Project timing: pilot line in 10 weeks
Initial concept assumptions: [paste Sales Engineer + Solutions Architect outputs]

Deliver:
1. likely long-lead items
2. outsourced fabrication risks
3. vendor dependencies that threaten schedule
4. recommended buy-early list
5. sourcing assumptions that must be visible before quotation
```

### Phase 3: Validation and Quality Gates

**Step 5 — Activate Test and Validation Engineer**

```text
Activate Test and Validation Engineer.

Inputs:
- requirement package: [paste]
- line concept: [paste]
- process industrialization notes: [paste]

Deliver:
1. proposed test strategy
2. critical checks by station
3. FAT / SAT evidence plan
4. golden sample and false-reject considerations
5. acceptance criteria gaps still needing customer confirmation
```

**Step 6 — Activate Quality and 8D Engineer**

```text
Activate Quality and 8D Engineer.

Inputs:
- requirement package: [paste]
- line concept: [paste]
- validation strategy: [paste]

Deliver:
1. top defect escape risks
2. containment ideas before launch
3. recurrence-prevention recommendations
4. quality assumptions that need to be written into technical agreement or acceptance criteria
```

### Phase 4: Pre-Quote Internal Review

**Step 7 — Run an internal review pack**

At this point, combine outputs from:
- Sales Engineer
- Solutions Architect
- Process Industrialization Engineer
- Sourcing Manager
- Test and Validation Engineer
- Quality and 8D Engineer

Use the combined package to produce:
- quotation precheck
- technical assumptions
- exclusions
- launch risks
- next-step workshop agenda with the customer

### Phase 5: Launch Planning and Commissioning Reality Check

**Step 8 — Activate Program Launch Manager**

```text
Activate Program Launch Manager.

Project target: pilot line in 10 weeks
Inputs:
- line concept: [paste]
- sourcing risk notes: [paste]
- validation strategy: [paste]
- quality risk notes: [paste]

Deliver:
1. milestone plan from concept freeze to FAT, SAT, and ramp
2. critical path risks
3. owner-by-owner action list
4. readiness gates that must be passed before next phase
```

**Step 9 — Activate Controls and Commissioning Engineer**

```text
Activate Controls and Commissioning Engineer.

Inputs:
- line concept: [paste]
- milestone plan: [paste]
- validation strategy: [paste]

Stress-test the commissioning reality.
Deliver:
1. startup and debug risks
2. sequence and alarm-recovery concerns
3. likely commissioning bottlenecks
4. what should be simulated or tested before on-site debug
```

### Phase 6: Serviceability and Ramp Readiness

**Step 10 — Activate After-Sales Service Engineer**

```text
Activate After-Sales Service Engineer.

Inputs:
- line concept: [paste]
- validation plan: [paste]
- commissioning risks: [paste]

Deliver:
1. serviceability concerns
2. likely field failure modes
3. remote troubleshooting considerations
4. what documentation or logs should exist before handover
```

**Step 11 — Activate Production Ramp Optimizer**

```text
Activate Production Ramp Optimizer.

Inputs:
- milestone plan: [paste]
- validation strategy: [paste]
- serviceability notes: [paste]
- commissioning notes: [paste]

Deliver:
1. ramp-up stabilization plan
2. launch-week monitoring metrics
3. micro-stop capture approach
4. escalation triggers if takt or yield misses target
```

## Suggested Deliverables at Each Gate

### Gate A — Before quotation
- requirement clarification sheet
- assumption log
- quote blockers and pricing-sensitive items

### Gate B — Before concept freeze
- station concept and process breakdown
- long-lead risk list
- initial validation logic

### Gate C — Before FAT
- acceptance logic
- debug/commissioning risk plan
- serviceability checklist

### Gate D — Before SAT / ramp
- launch plan
- on-site escalation matrix
- ramp metrics dashboard outline

## Key Patterns

1. Sequential handoffs: each agent sharpens the opportunity from a different function
2. Parallel work: concept, process, and sourcing can advance together early
3. Quality gates: test, quality, and commissioning agents stop weak assumptions from becoming expensive surprises
4. Operational realism: after-sales and ramp agents force the team to think beyond FAT success
5. Context passing matters: always feed full outputs forward instead of summarizing too aggressively

## Tips

- Start with the Sales Engineer even if the customer request feels technical — bad quoting usually begins with unclear scope, not weak hardware.
- Run Sourcing early on short schedules; long-lead blindness can invalidate a beautiful concept.
- Treat the Controls and Commissioning Engineer as a reality gate, not as a late-stage fixer.
- Pull in After-Sales and Ramp agents before handover, not after the first field failure.
- Use this workflow with the Manufacturing Presales Template Pack when you want a more structured set of forms and working artifacts.