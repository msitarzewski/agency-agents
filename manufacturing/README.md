# Manufacturing Division

The Manufacturing Division is built for non-standard automation equipment, semi-automatic cells, custom stations, linked production lines, launch support, and post-installation stabilization work.

This division is especially well suited to:
- automotive electronics manufacturing
- home appliance manufacturing
- test stations, assembly lines, inspection cells, and retrofit projects
- projects where technical scope, quotation assumptions, launch timing, and field stability are tightly connected

## Agents in This Division

| Agent | Best used for | Main output |
|-------|---------------|-------------|
| [Non-Standard Automation Sales Engineer](./manufacturing-nonstandard-automation-sales-engineer.md) | Early customer discovery, vague RFQs, quotation readiness | requirement summary, open-question list, assumption block, next-step recommendation |
| [Automation Solutions Architect](./manufacturing-automation-solutions-architect.md) | First-pass line concept, station breakdown, scope framing | concept architecture, station map, interface list, technical assumptions |
| [Test and Validation Engineer](./manufacturing-test-and-validation-engineer.md) | Acceptance logic, FAT/SAT planning, test coverage | validation strategy, test matrix, evidence plan, acceptance gaps |
| [Process Industrialization Engineer](./manufacturing-process-industrialization-engineer.md) | Converting manual process into scalable automation flow | process breakdown, industrialization logic, bottleneck analysis, mixed-model concerns |
| [Quality and 8D Engineer](./manufacturing-quality-8d-engineer.md) | Launch quality, complaints, recurrence prevention | containment logic, defect framing, root-cause paths, corrective-action structure |
| [Program Launch Manager](./manufacturing-program-launch-manager.md) | Cross-functional project coordination from concept to launch | milestone plan, owner matrix, readiness gates, launch risk list |
| [Controls and Commissioning Engineer](./manufacturing-controls-and-commissioning-engineer.md) | PLC/debug/startup/alarm recovery/line sequencing | commissioning risk list, startup logic review, alarm handling guidance, debug priorities |
| [Sourcing and Supplier Coordination Manager](./manufacturing-sourcing-and-supplier-coordination-manager.md) | Long-lead tracking, outsourcing risk, supplier follow-up | sourcing risk list, buy-early recommendations, blocker visibility |
| [After-Sales Service Engineer](./manufacturing-after-sales-service-engineer.md) | Field recovery, repeated faults, install-base support | troubleshooting structure, service action plan, recurrence capture, knowledge handoff |
| [Production Ramp Optimizer](./manufacturing-production-ramp-optimizer.md) | Post-launch stabilization, takt recovery, micro-stop reduction | ramp plan, monitoring metrics, stabilization priorities, escalation triggers |

## Recommended Usage Sequence

### 1. Customer request arrives
Start with:
- Non-Standard Automation Sales Engineer

Why:
- turns unclear customer language into engineering-usable scope
- separates facts, assumptions, exclusions, and blockers before quoting

### 2. First-pass concept shaping
Then bring in:
- Automation Solutions Architect
- Process Industrialization Engineer
- Sourcing and Supplier Coordination Manager

Why:
- architect defines the likely machine or line structure
- industrialization engineer tests whether the process can really be automated at target takt
- sourcing manager exposes long-lead and outsourced-part schedule risk early

### 3. Validation and quality gate
Then bring in:
- Test and Validation Engineer
- Quality and 8D Engineer

Why:
- test engineer defines what “pass” means
- quality engineer surfaces defect escape and recurrence risk before launch, not after complaints begin

### 4. Launch planning and debug realism
Then bring in:
- Program Launch Manager
- Controls and Commissioning Engineer

Why:
- launch manager turns concept into milestones, gates, and owners
- commissioning engineer pressure-tests startup, sequence, alarm recovery, and debug feasibility

### 5. Handover and stabilization
Then bring in:
- After-Sales Service Engineer
- Production Ramp Optimizer

Why:
- service engineer ensures the system is supportable in the field
- ramp optimizer focuses on sustained takt, yield, and micro-stop reduction after installation

## Typical Collaboration Patterns

### Pattern A — Presales / RFQ response
Use:
- Sales Engineer
- Solutions Architect
- Sourcing Manager
- Test and Validation Engineer

Best for:
- RFQs, customer visits, early budget quotations, concept clarification

### Pattern B — Internal technical review before quote release
Use:
- Sales Engineer
- Solutions Architect
- Process Industrialization Engineer
- Test and Validation Engineer
- Quality and 8D Engineer
- Sourcing Manager

Best for:
- deciding whether quotation is credible
- exposing assumption gaps and under-quoted risks

### Pattern C — FAT / SAT / commissioning preparation
Use:
- Program Launch Manager
- Controls and Commissioning Engineer
- Test and Validation Engineer
- Quality and 8D Engineer

Best for:
- launch readiness
- debug planning
- acceptance preparation

### Pattern D — Post-installation recovery and ramp-up
Use:
- After-Sales Service Engineer
- Production Ramp Optimizer
- Quality and 8D Engineer
- Controls and Commissioning Engineer

Best for:
- repeated faults
- unstable takt
- low yield after handover
- difficult launch weeks

## Shared References

- [Manufacturing Shared Glossary and Boundaries](./GLOSSARY.md)
- [Manufacturing Scenario Playbook](./SCENARIO-PLAYBOOK.md)
- [Manufacturing Cross-Agent Handoff Templates](./HANDOFF-TEMPLATES.md)

## Example Workflows

- [Manufacturing Presales Template Pack](../examples/manufacturing-presales-template-pack.md)
- [Multi-Agent Workflow: Manufacturing RFQ to Launch Readiness](../examples/workflow-manufacturing-rfq.md)

## Practical Tips

1. Do not start with the most technical agent just because the customer sent drawings. In non-standard automation, early failure usually comes from unclear boundaries, not from missing hardware ideas.
2. Always surface assumptions explicitly before quotation.
3. Run sourcing risk early on compressed schedules.
4. Treat FAT success and production success as different problems — use ramp and service agents before customer complaints force you to.
5. Pass full context between agents. Their value compounds when each one sees the previous outputs, not a one-line summary.

## If You Only Activate 3 Agents

For the highest-value starter combination, use:
1. Non-Standard Automation Sales Engineer
2. Automation Solutions Architect
3. Program Launch Manager

That combination usually gives the best first-pass balance of:
- requirement clarity
- concept structure
- project execution realism