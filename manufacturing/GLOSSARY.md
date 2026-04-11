# Manufacturing Shared Glossary and Boundaries

This glossary keeps the Manufacturing Division aligned on common factory terms, decision gates, and operating boundaries.

Use it when you want the 10 manufacturing agents to sound like one coordinated team instead of 10 unrelated specialists.

## Core Throughput Terms

### Takt Time
The required production rhythm needed to meet customer demand.

Use it to answer:
- how fast each unit must leave the system
- whether the proposed station count and automation level are realistic

Do not confuse with:
- actual cycle time
- machine-only motion time
- average output over a shift with downtime hidden inside it

### Cycle Time (CT)
The actual time required for one process, station, or machine to complete one unit or one loop.

Practical rule:
- if CT > takt, the station is a bottleneck unless offset by parallelization, buffering, or different routing logic

### UPH / CPH
Units per hour / cycles per hour.

Use when customers speak in output rather than seconds.
Always clarify:
- whether the figure is net or gross
- whether it assumes ideal running or includes losses

### OEE
Overall Equipment Effectiveness. Usually combines availability, performance, and quality.

In this division, treat OEE as a useful target indicator, not as a magic substitute for line-specific bottleneck analysis.

## Yield and Quality Terms

### First-Pass Yield (FPY)
The percentage of units that pass without rework.

Important because:
- a line can appear to meet output while quietly burning labor and time in rework loops
- launch performance often collapses when FPY assumptions were too optimistic

### False Reject
A good part incorrectly failed by a test or inspection process.

This matters heavily in automated validation because false reject pain can destroy operator trust, line rhythm, and launch stability.

### CTQ
Critical to Quality. The dimensions, characteristics, or functions that most directly determine whether the product is acceptable.

Manufacturing agents should always ask:
- which CTQs matter most
- where each CTQ is created
- where it is verified
- what happens when it is out of spec

### Containment
Immediate action to stop suspected defects from escaping further downstream or reaching the customer.

Containment is not root cause.
Containment is the first safety wall.

### 8D / CAPA
Structured problem-solving and corrective-action methods used when quality issues, customer complaints, or repeated failures occur.

Use when the problem requires:
- team ownership
- documented root-cause reasoning
- permanent corrective action
- recurrence prevention

## Delivery and Acceptance Terms

### FAT
Factory Acceptance Test — usually performed before shipment, at the supplier side.

Typical purpose:
- verify basic function
- confirm sequence logic
- demonstrate major process steps
- prove agreed acceptance points before the line leaves the builder

Boundary reminder:
FAT success does not guarantee successful site integration or stable production ramp.

### SAT
Site Acceptance Test — performed after installation at the customer site.

Typical purpose:
- verify the line in real site conditions
- confirm utility, product, operator, and interface reality
- validate customer acceptance in the actual operating environment

### Commissioning
The startup, debug, sequencing, tuning, alarm-recovery, and stabilization work required to bring a machine or line from installed hardware to repeatable production behavior.

Do not reduce commissioning to "power on and run."
For non-standard automation, commissioning often reveals the truth of the concept.

### Ramp-Up
The period after installation or SAT where the line must move from first success to stable takt, stable yield, and repeatable daily output.

Ramp-up is where many hidden weaknesses appear:
- micro-stops
- unstable feeders
- parameter drift
- false rejects
- operator workarounds
- weak recovery from alarms

## Traceability and Integration Terms

### Traceability
The ability to connect each unit or batch to relevant process, operator, station, test, or material records.

Always clarify:
- unit-level or batch-level traceability
- required data fields
- retention period
- where the data must live
- whether the line must block on missing traceability events

### MES Integration
Connection between the machine/line and customer manufacturing-execution systems.

Never leave MES integration as a vague yes/no item.
Clarify:
- what data is exchanged
- who owns the API/protocol definition
- whether handshake timing affects takt
- what happens when MES is unavailable

### Barcode / RFID
Identity carriers used for part or process tracking.

The important question is not just which technology is used, but:
- when and where identity is created
- what happens when a code is missing, unreadable, or duplicated

## Changeover and Model-Mix Terms

### Changeover
The time and work needed to switch the machine or line from one product variant to another.

For mixed-model lines, changeover is often one of the biggest hidden quotation and launch risks.
Always clarify:
- manual vs automatic changeover content
- tooling swaps
- parameter recipe switching
- vision/test recipe switching
- operator skill dependency

### Mixed-Model Production
Running multiple variants, SKUs, or families on the same equipment or line.

Important because mixed-model complexity affects:
- fixture strategy
- feeder design
- recipe logic
- test-program management
- takt stability
- error-proofing

## Sourcing and Execution Terms

### Long-Lead Item
A part, subsystem, or outsourced activity whose procurement or fabrication lead time can threaten the project schedule.

Examples:
- robots
- vision hardware
- servo systems
- custom machined structures
- electrical cabinets
- customer-specified imported parts

### Outsourced Fabrication
Mechanical or special-process work completed by outside suppliers rather than internally.

Always examine:
- tolerance capability
- response speed
- revision responsiveness
- incoming-quality stability

### Buy-Early Item
A part or subsystem that should be purchased before all design details are fully frozen because schedule risk is greater than revision risk.

Use carefully — only when assumptions are explicit and ownership is clear.

## Operating Boundaries Between Agents

### Sales Engineer boundary
Owns:
- requirement clarification
- quotation-readiness framing
- assumptions and exclusions visibility

Does not own alone:
- detailed station architecture
- final validation logic
- final commissioning planning

### Solutions Architect boundary
Owns:
- concept structure
- station and interface framing
- automation boundary design

Does not own alone:
- supplier schedule reality
- full validation evidence plan
- launch milestone governance

### Test and Validation boundary
Owns:
- test logic
- evidence logic
- FAT/SAT validation structure

Does not own alone:
- commercial assumptions
- supplier expediting
- post-launch output stabilization

### Process Industrialization boundary
Owns:
- process breakdown
- bottleneck logic
- manual-to-automation translation

Does not own alone:
- detailed PLC strategy
- customer-facing commercial negotiation

### Quality and 8D boundary
Owns:
- containment thinking
- defect framing
- corrective/preventive logic

Does not own alone:
- project schedule control
- sourcing ownership

### Program Launch Manager boundary
Owns:
- milestone structure
- owner matrix
- readiness gates
- cross-functional escalation

Does not own alone:
- deep station design
- root-cause technical detail in every domain

### Controls and Commissioning boundary
Owns:
- startup realism
- sequence logic concerns
- alarm-recovery practicality
- debug priorities

Does not own alone:
- quotation strategy
- supplier commercial control

### Sourcing and Supplier Coordination boundary
Owns:
- long-lead visibility
- supplier blocker exposure
- buy-early logic

Does not own alone:
- line concept architecture
- acceptance logic

### After-Sales boundary
Owns:
- serviceability
- field troubleshooting structure
- recurring-problem knowledge capture

Does not own alone:
- initial concept architecture
- sourcing schedule control

### Ramp Optimizer boundary
Owns:
- post-launch stability
- micro-stop reduction
- takt/yield recovery rhythm

Does not own alone:
- early RFQ clarification
- FAT evidence design

## Shared Rules for the Whole Division

1. Do not hide uncertainty. Missing inputs must be surfaced clearly.
2. Do not confuse FAT success with production success.
3. Do not discuss takt without clarifying the basis.
4. Do not discuss traceability as a buzzword — specify data, timing, ownership, and failure behavior.
5. Do not assume mixed-model flexibility is cheap.
6. Do not let commissioning become a catch-all for unresolved concept mistakes.
7. Do not wait until customer complaints to involve service and ramp thinking.

## Recommended Companion Docs

- [Manufacturing Division README](./README.md)
- [Manufacturing Presales Template Pack](../examples/manufacturing-presales-template-pack.md)
- [Multi-Agent Workflow: Manufacturing RFQ to Launch Readiness](../examples/workflow-manufacturing-rfq.md)