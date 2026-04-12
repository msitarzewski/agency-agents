# Manufacturing Scenario Playbook

This playbook helps you choose the right Manufacturing Division agents for the most common real-world situations in non-standard automation projects.

Primary business fit for this division:
- automotive electronics
- home appliances

Use those as the default industry lens unless a scenario explicitly says otherwise.

## Scenario 1: New Line Introduction

### Typical situation
A customer is launching a new product or new factory line and needs a fresh automation concept, often under schedule pressure and with incomplete process maturity.

### Main risks
- product/process still changing
- takt assumptions are optimistic
- validation logic not yet mature
- long-lead parts missed too late
- FAT passes but launch struggles

### Best agent combination
1. Non-Standard Automation Sales Engineer
2. Automation Solutions Architect
3. Process Industrialization Engineer
4. Test and Validation Engineer
5. Program Launch Manager
6. Sourcing and Supplier Coordination Manager

### Best outputs
- clarified requirement pack
- line concept and station map
- industrialization risk notes
- validation strategy
- milestone and sourcing risk view

### Recommended sequence
- Sales Engineer
- Solutions Architect + Process Industrialization + Sourcing Manager in parallel
- Test and Validation Engineer
- Program Launch Manager

### Watch-outs
- do not quote around unstable process assumptions
- do not leave acceptance logic until after mechanical design has progressed too far
- do not delay long-lead review

## Scenario 2: Retrofit / Existing Line Upgrade

### Typical situation
The customer already has a line or station, but it is unstable, too manual, too slow, or missing traceability and quality controls.

### Main risks
- actual site conditions differ from drawings
- legacy equipment interfaces are weak or undocumented
- change window is short
- old process weaknesses get carried into the new design

### Best agent combination
1. Non-Standard Automation Sales Engineer
2. Automation Solutions Architect
3. Controls and Commissioning Engineer
4. Process Industrialization Engineer
5. Quality and 8D Engineer

### Best outputs
- retrofit scope boundary
- upstream/downstream interface clarification
- debug and downtime-risk view
- process bottleneck analysis
- defect containment considerations during transition

### Recommended sequence
- Sales Engineer
- Solutions Architect
- Process Industrialization Engineer + Controls and Commissioning Engineer
- Quality and 8D Engineer

### Watch-outs
- do not assume old line data is trustworthy
- do not ignore temporary bypass or manual fallback needs
- do not underestimate shutdown and restart complexity

## Scenario 3: Customer Complaint / 8D Pressure

### Typical situation
A customer reports repeated defects, instability, missed inspections, or poor recovery after alarms and expects a structured response.

### Main risks
- containment is too weak
- teams jump to root cause before protecting output
- repeated failures are treated as isolated incidents
- service knowledge is not captured for reuse

### Best agent combination
1. Quality and 8D Engineer
2. After-Sales Service Engineer
3. Controls and Commissioning Engineer
4. Test and Validation Engineer
5. Production Ramp Optimizer

### Best outputs
- containment plan
- defect framing and recurrence path
- troubleshooting sequence
- validation gap analysis
- stabilization plan after corrective action

### Recommended sequence
- Quality and 8D Engineer
- After-Sales Service Engineer
- Controls and Commissioning Engineer
- Test and Validation Engineer
- Production Ramp Optimizer

### Watch-outs
- containment first, root cause second
- avoid hand-wavy blame on operators without data
- verify whether false reject logic is part of the complaint pattern

## Scenario 4: Field Service / Emergency Recovery

### Typical situation
The line is down or unstable at the customer site. Output is threatened and the team needs fast recovery, not a long PowerPoint.

### Main risks
- no structured triage
- repeated alarms with no durable fix
- unclear ownership between service, controls, and production
- local workarounds hide the true failure mode

### Best agent combination
1. After-Sales Service Engineer
2. Controls and Commissioning Engineer
3. Quality and 8D Engineer
4. Program Launch Manager

### Best outputs
- triage sequence
- probable failure buckets
- alarm and recovery logic review
- escalation path and owner matrix

### Recommended sequence
- After-Sales Service Engineer
- Controls and Commissioning Engineer
- Quality and 8D Engineer if escape or defect risk exists
- Program Launch Manager if the issue threatens larger milestone commitments

### Watch-outs
- restore safe output first, but capture evidence before it disappears
- do not leave service learnings trapped in chat history or oral handoff
- separate temporary recovery from permanent corrective action

## Scenario 5: Production Ramp-Up and Stabilization

### Typical situation
FAT and installation are complete, but the line is not yet producing at stable takt, stable yield, or stable uptime.

### Main risks
- micro-stops not captured systematically
- takt measured selectively rather than honestly
- false rejects and operator workarounds distort reality
- service and launch teams leave too early

### Best agent combination
1. Production Ramp Optimizer
2. Controls and Commissioning Engineer
3. Test and Validation Engineer
4. After-Sales Service Engineer
5. Quality and 8D Engineer

### Best outputs
- ramp dashboard logic
- micro-stop capture method
- escalation triggers for takt/yield misses
- recovery priorities
- recurrence-prevention actions

### Recommended sequence
- Production Ramp Optimizer
- Controls and Commissioning Engineer
- Test and Validation Engineer
- After-Sales Service Engineer
- Quality and 8D Engineer

### Watch-outs
- do not confuse one good shift with true stability
- track both output loss and recovery behavior
- keep defect, alarm, and takt data tied together rather than reviewing them in separate silos

## Quick Selection Matrix

| Situation | Start with | Add next | Typical goal |
|---|---|---|---|
| New line introduction | Sales Engineer | Solutions Architect + Process Industrialization + Sourcing | turn vague need into credible concept and launch plan |
| Existing line retrofit | Sales Engineer | Solutions Architect + Controls | define safe, realistic retrofit scope |
| Customer complaint / 8D | Quality and 8D Engineer | After-Sales + Controls | contain escapes and stop recurrence |
| Field service emergency | After-Sales Service Engineer | Controls + Quality | restore safe output fast |
| Ramp-up instability | Production Ramp Optimizer | Controls + Test | stabilize takt, yield, and uptime |

## Shared Advice Across All Scenarios

1. Pick agents based on the project phase, not just on titles.
2. Use the Sales Engineer earlier than intuition suggests; unclear boundaries usually create downstream pain.
3. Pull in Controls and Commissioning before site debug becomes a crisis.
4. Bring Sourcing in whenever schedule compression exists.
5. Use After-Sales and Ramp agents before handover whenever possible; late activation is expensive.

## Companion Docs

- [Manufacturing Division README](./README.md)
- [Manufacturing Shared Glossary and Boundaries](./GLOSSARY.md)
- [Manufacturing Presales Template Pack](../examples/manufacturing-presales-template-pack.md)
- [Multi-Agent Workflow: Manufacturing RFQ to Launch Readiness](../examples/workflow-manufacturing-rfq.md)