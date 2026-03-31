# Source Index

- Source: `/Volumes/disk1/go/src/agency-agents/strategy/runbooks/scenario-incident-response.md`
- Unit count: `30`

| unit_id | source_hash | unit_type | excerpt |
| --- | --- | --- | --- |
| U001 | 265b397bcb45 | heading | # 🚨 Runbook: Incident Response |
| U002 | 70d09d8a3226 | paragraph | > **Mode**: NEXUS-Micro \| **Duration**: Minutes to hours \| **Agents**: 3-8 |
| U003 | 58b63e273b96 | paragraph | --- |
| U004 | 759150cde127 | heading | ## Scenario |
| U005 | 008b1db276ff | paragraph | Something is broken in production. Users are affected. Speed of response matters, but so does doing it right. This runbook covers detection through post-mortem. |
| U006 | 4258da443ed7 | heading | ## Severity Classification |
| U007 | cfe6b45a1fdc | paragraph | \| Level \| Definition \| Examples \| Response Time \| \|-------\|-----------\|----------\|--------------\| \| **P0 — Critical** \| Service completely down, data loss, secu |
| U008 | c5375b28ce4b | heading | ## Response Teams by Severity |
| U009 | 55ad948b403e | heading | ### P0 — Critical Response Team \| Agent \| Role \| Action \| \|-------\|------\|--------\| \| **Infrastructure Maintainer** \| Incident commander \| Assess scope, coordin |
| U010 | 624db41f6bf0 | heading | ### P1 — High Response Team \| Agent \| Role \| \|-------\|------\| \| **Infrastructure Maintainer** \| Incident commander \| \| **DevOps Automator** \| Deployment support |
| U011 | d8b9ce6f57b5 | heading | ### P2 — Medium Response \| Agent \| Role \| \|-------\|------\| \| **Relevant Developer Agent** \| Fix implementation \| \| **Evidence Collector** \| Verify fix \| |
| U012 | 5949c02c89bd | heading | ### P3 — Low Response \| Agent \| Role \| \|-------\|------\| \| **Sprint Prioritizer** \| Add to backlog \| |
| U013 | 3bda48ca33b1 | heading | ## Incident Response Sequence |
| U014 | feea494b8843 | heading | ### Step 1: Detection & Triage (0-5 minutes) |
| U015 | c2bbdaee63ed | code | ``` TRIGGER: Alert from monitoring / User report / Agent detection Infrastructure Maintainer: 1. Acknowledge alert 2. Assess scope and impact - How many users a |
| U016 | a40423435757 | heading | ### Step 2: Investigation (5-30 minutes) |
| U017 | 08a0ffadc1f3 | code | ``` PARALLEL INVESTIGATION: Infrastructure Maintainer: ├── Check system metrics (CPU, memory, network, disk) ├── Review error logs ├── Check recent deployments  |
| U018 | 53eac05bee9c | heading | ### Step 3: Mitigation (15-60 minutes) |
| U019 | 9b85bc843ccb | code | ``` DECISION TREE: IF caused by recent deployment: → DevOps Automator: Execute rollback → Infrastructure Maintainer: Verify recovery → Evidence Collector: Confi |
| U020 | 67d6b0876eb3 | heading | ### Step 4: Resolution Verification (Post-fix) |
| U021 | c1f7d57fdb25 | code | ``` Evidence Collector: 1. Verify the fix resolves the issue 2. Screenshot evidence of working state 3. Confirm no new issues introduced Infrastructure Maintain |
| U022 | fa4ece4f2b92 | heading | ### Step 5: Post-Mortem (Within 48 hours) |
| U023 | 8dcad9efcbf0 | code | ``` Workflow Optimizer leads post-mortem: 1. Timeline reconstruction - When was the issue introduced? - When was it detected? - When was it resolved? - Total us |
| U024 | 837859433c90 | heading | ## Communication Templates |
| U025 | 6c94e2571c3d | heading | ### Status Page Update (Support Responder) |
| U026 | 509534c2ff11 | code | ``` [TIMESTAMP] — [SERVICE NAME] Incident Status: [Investigating / Identified / Monitoring / Resolved] Impact: [Description of user impact] Current action: [Wha |
| U027 | 87409e9089d0 | heading | ### Executive Update (Executive Summary Generator — P0 only) |
| U028 | 0a29b6b85a60 | code | ``` INCIDENT BRIEF — [TIMESTAMP] SITUATION: [Service] is [down/degraded] affecting [N users/% of traffic] CAUSE: [Known/Under investigation] — [Brief descriptio |
| U029 | c807aaeafb8b | heading | ## Escalation Matrix |
| U030 | f76be923c648 | paragraph | \| Condition \| Escalate To \| Action \| \|-----------\|------------\|--------\| \| P0 not resolved in 30 min \| Studio Producer \| Additional resources, vendor escalation |
