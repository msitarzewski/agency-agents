# Source Index

- Source: `/Volumes/disk1/go/src/agency-agents/strategy/coordination/handoff-templates.md`
- Unit count: `33`

| unit_id | source_hash | unit_type | excerpt |
| --- | --- | --- | --- |
| U001 | d87ad3f16bd3 | heading | # 📋 NEXUS Handoff Templates |
| U002 | 19d5709c4eac | paragraph | > Standardized templates for every type of agent-to-agent handoff in the NEXUS pipeline. Consistent handoffs prevent context loss — the #1 cause of multi-agent  |
| U003 | 58b63e273b96 | paragraph | --- |
| U004 | a47c201fc228 | heading | ## 1. Standard Handoff Template |
| U005 | 4ae843ea7e21 | paragraph | Use for any agent-to-agent work transfer. |
| U006 | beecb6a7906c | code | ```markdown # NEXUS Handoff Document ## Metadata \| Field \| Value \| \|-------\|-------\| \| **From** \| [Agent Name] ([Division]) \| \| **To** \| [Agent Name] ([Division |
| U007 | 58b63e273b96 | paragraph | --- |
| U008 | 6d09f40c38e8 | heading | ## 2. QA Feedback Loop — PASS |
| U009 | c46b0b138e3b | paragraph | Use when Evidence Collector or other QA agent approves a task. |
| U010 | 32965133194e | code | ```markdown # NEXUS QA Verdict: PASS ✅ ## Task \| Field \| Value \| \|-------\|-------\| \| **Task ID** \| [ID] \| \| **Task Description** \| [Description] \| \| **Developer |
| U011 | 58b63e273b96 | paragraph | --- |
| U012 | d0c167e24db2 | heading | ## 3. QA Feedback Loop — FAIL |
| U013 | ec78be78ab5f | paragraph | Use when Evidence Collector or other QA agent rejects a task. |
| U014 | 391009ecf0c5 | code | ```markdown # NEXUS QA Verdict: FAIL ❌ ## Task \| Field \| Value \| \|-------\|-------\| \| **Task ID** \| [ID] \| \| **Task Description** \| [Description] \| \| **Developer |
| U015 | 58b63e273b96 | paragraph | --- |
| U016 | 960a0fabb8ae | heading | ## 4. Escalation Report |
| U017 | b93496e29b4e | paragraph | Use when a task exceeds 3 retry attempts. |
| U018 | fbe5bd84d556 | code | ```markdown # NEXUS Escalation Report 🚨 ## Task \| Field \| Value \| \|-------\|-------\| \| **Task ID** \| [ID] \| \| **Task Description** \| [Description] \| \| **Develope |
| U019 | 58b63e273b96 | paragraph | --- |
| U020 | b439d50e6270 | heading | ## 5. Phase Gate Handoff |
| U021 | da59262133ce | paragraph | Use when transitioning between NEXUS phases. |
| U022 | 38fef4a22692 | code | ```markdown # NEXUS Phase Gate Handoff ## Transition \| Field \| Value \| \|-------\|-------\| \| **From Phase** \| Phase [N] — [Name] \| \| **To Phase** \| Phase [N+1] —  |
| U023 | 58b63e273b96 | paragraph | --- |
| U024 | 77a0ac5feab9 | heading | ## 6. Sprint Handoff |
| U025 | 008e8cc66f90 | paragraph | Use at sprint boundaries. |
| U026 | 55ee33363a5b | code | ```markdown # NEXUS Sprint Handoff ## Sprint Summary \| Field \| Value \| \|-------\|-------\| \| **Sprint** \| [Number] \| \| **Duration** \| [Start date] → [End date] \|  |
| U027 | 58b63e273b96 | paragraph | --- |
| U028 | 36f7bb981ab7 | heading | ## 7. Incident Handoff |
| U029 | 568d6cc6d7b6 | paragraph | Use during incident response. |
| U030 | 8d356b211f16 | code | ```markdown # NEXUS Incident Handoff ## Incident \| Field \| Value \| \|-------\|-------\| \| **Severity** \| [P0 / P1 / P2 / P3] \| \| **Detected by** \| [Agent or system |
| U031 | 58b63e273b96 | paragraph | --- |
| U032 | 317fb522497d | heading | ## Usage Guide |
| U033 | 29217ca78be8 | paragraph | \| Situation \| Template to Use \| \|-----------\|----------------\| \| Assigning work to another agent \| Standard Handoff (#1) \| \| QA approves a task \| QA PASS (#2) \| |
