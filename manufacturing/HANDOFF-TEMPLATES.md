# Manufacturing Cross-Agent Handoff Templates

Use these templates when one Manufacturing Division agent hands work to another.

Goal:
- keep context complete
- reduce rework caused by missing assumptions
- make the 10 manufacturing agents feel like one coordinated team

## General Handoff Rules

Every handoff should try to include:
- current objective
- confirmed facts
- working assumptions
- unresolved questions
- top risks
- expected output from the next agent
- timing pressure or milestone impact

Do not hand off only a vague summary like:
- "please continue this"
- "customer wants automation"
- "line unstable, help"

---

## 1. Sales Engineer → Solutions Architect

### When to use
After customer discovery is good enough to sketch a first-pass concept.

### Template
```text
Activate Automation Solutions Architect.

Here is the handoff from Sales Engineer.

Project:
- Customer / industry:
- Product / process:
- Project type: station / cell / line / retrofit
- Customer goal:
- Target takt / UPH:
- Labor target:
- Timeline:

Confirmed facts:
- 
- 
- 

Working assumptions:
- 
- 
- 

Open questions:
- 
- 
- 

Commercial / technical risks:
- 
- 
- 

Please deliver:
1. first-pass station architecture
2. process boundaries and manual/automatic split
3. upstream/downstream interface assumptions
4. key technical decisions
5. blockers to concept freeze
```

---

## 2. Sales Engineer → Sourcing Manager

### When to use
When quotation timing is tight or the concept clearly includes long-lead or outsourced items.

### Template
```text
Activate Sourcing and Supplier Coordination Manager.

Here is the handoff from Sales Engineer.

Project timing:
- RFQ due date:
- target FAT / SAT / launch timing:

Known hardware / supplier-sensitive scope:
- 
- 
- 

Customer brand constraints:
- 

Known assumptions:
- 
- 

Unknowns still open:
- 
- 

Please deliver:
1. likely long-lead list
2. outsourced fabrication risks
3. buy-early candidates
4. supplier blockers that threaten quote or schedule
5. sourcing assumptions that must be exposed before quotation
```

---

## 3. Solutions Architect → Test and Validation Engineer

### When to use
When concept shape is clear enough to define validation logic and acceptance structure.

### Template
```text
Activate Test and Validation Engineer.

Here is the handoff from Solutions Architect.

Line concept summary:
- Station 1:
- Station 2:
- Station 3:
- Key interfaces:

Critical process risks:
- 
- 

CTQs / quality concerns:
- 
- 

Known customer acceptance expectations:
- 
- 

Open questions:
- 
- 

Please deliver:
1. validation strategy by phase
2. acceptance criteria matrix
3. sample governance needs
4. false-reject / escape concerns
5. evidence required for FAT and SAT
```

---

## 4. Solutions Architect → Controls and Commissioning Engineer

### When to use
When the line concept needs startup/debug realism and sequence pressure-testing.

### Template
```text
Activate Controls and Commissioning Engineer.

Here is the handoff from Solutions Architect.

Concept summary:
- line/station structure:
- machine modes:
- major interfaces:
- critical device groups:

Expected sequence challenges:
- 
- 

Known assumptions:
- 
- 

Known weak spots / open items:
- 
- 

Please deliver:
1. startup/debug risk list
2. likely sequence and alarm-recovery weaknesses
3. commissioning priorities by phase
4. pre-site simulation or test recommendations
5. logic gaps that could threaten stable repeat cycles
```

---

## 5. Process Industrialization Engineer → Quality and 8D Engineer

### When to use
When process analysis shows likely escape paths, weak controls, or repeatability risks.

### Template
```text
Activate Quality and 8D Engineer.

Here is the handoff from Process Industrialization Engineer.

Current process and bottlenecks:
- 
- 

Likely failure modes:
- 
- 

Where process variation is highest:
- 
- 

Current controls / inspection points:
- 
- 

Please deliver:
1. defect escape risk framing
2. containment recommendations
3. root-cause directions to monitor
4. recurrence-prevention priorities
5. what should be added to validation or acceptance logic
```

---

## 6. Test and Validation Engineer → Program Launch Manager

### When to use
When launch planning needs validation gates, sample readiness, and acceptance logic integrated into milestones.

### Template
```text
Activate Program Launch Manager.

Here is the handoff from Test and Validation Engineer.

Validation status:
- current phase:
- what is frozen:
- what is not frozen:

Acceptance dependencies:
- sample readiness:
- criteria freeze:
- challenge-set readiness:
- traceability proof points:

Top validation risks:
- 
- 
- 

Please deliver:
1. milestone impacts
2. launch blockers related to validation readiness
3. owner/action plan
4. escalation timing
5. customer-facing status summary if needed
```

---

## 7. Controls and Commissioning Engineer → After-Sales Service Engineer

### When to use
When handover is approaching or repeated debug pain suggests future service exposure.

### Template
```text
Activate After-Sales Service Engineer.

Here is the handoff from Controls and Commissioning Engineer.

Commissioning history:
- top debug issues:
- unstable alarms:
- known recovery-sensitive stations:

Current workaround status:
- 
- 

Evidence / logs available:
- 
- 

Likely field-risk items:
- 
- 

Please deliver:
1. serviceability concerns
2. likely field failure buckets
3. remote troubleshooting requirements
4. what should be documented before handover
5. install-base risk notes
```

---

## 8. After-Sales Service Engineer → Quality and 8D Engineer

### When to use
When field issues show repeated failures, customer complaints, or likely systemic escapes.

### Template
```text
Activate Quality and 8D Engineer.

Here is the handoff from After-Sales Service Engineer.

Service issue summary:
- station / subsystem:
- symptom:
- customer impact:
- frequency / recurrence pattern:

Evidence captured:
- alarms / logs:
- photo/video:
- affected variants / lots:

Temporary recovery actions:
- 
- 

Please deliver:
1. structured problem description
2. containment logic
3. likely escape / recurrence path
4. corrective-action direction
5. what additional evidence is still needed
```

---

## 9. Program Launch Manager → Production Ramp Optimizer

### When to use
When SAT or handover is near complete and the focus shifts from launch event to stable daily output.

### Template
```text
Activate Production Ramp Optimizer.

Here is the handoff from Program Launch Manager.

Launch status:
- FAT status:
- SAT status:
- remaining open items:
- customer pressure points:

Current production risks:
- takt risk:
- yield risk:
- recovery risk:
- staffing / operating risk:

Known launch-week pain points:
- 
- 

Please deliver:
1. ramp stabilization plan
2. top loss buckets to monitor
3. daily/shift metrics to track
4. escalation triggers
5. cross-functional priorities for the first stable production window
```

---

## 10. Ramp Optimizer → Service / Controls / Quality Loopback

### When to use
When ramp data shows the line is not stabilizing and targeted intervention is needed.

### Template
```text
Activate [After-Sales Service Engineer / Controls and Commissioning Engineer / Quality and 8D Engineer].

Here is the handoff from Production Ramp Optimizer.

Ramp status:
- target vs actual UPH:
- target vs actual yield:
- top downtime categories:
- micro-stop pattern:

What appears systemic:
- 
- 

What appears local / recoverable:
- 
- 

Most urgent business impact:
- 

Please deliver:
1. focused corrective-action priorities
2. probable root-cause buckets in your specialty
3. immediate stabilization actions
4. medium-term prevention actions
5. what evidence or ownership is still missing
```

---

## Best Practice

If time allows, pass the full previous output into the next agent and place the handoff template above it.

Good pattern:
- short structured handoff
- then full source context pasted below

That usually produces better continuity than either:
- only a short summary
- or only a raw dump with no framing
