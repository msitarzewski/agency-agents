# Source Index

- Source: `/Volumes/disk1/go/src/agency-agents-worktrees/openclaw-normalize-20260325/strategy/playbooks/phase-3-build.md`
- Unit count: `48`

| unit_id | source_hash | unit_type | excerpt |
| --- | --- | --- | --- |
| U001 | 95dbc17f016b | heading | # 🔨 Phase 3 Playbook — Build & Iterate |
| U002 | 30f5d96c916b | paragraph | > **Duration**: 2-12 weeks (varies by scope) \| **Agents**: 15-30+ \| **Gate Keeper**: Agents Orchestrator |
| U003 | 58b63e273b96 | paragraph | --- |
| U004 | 1618c17e187b | heading | ## Objective |
| U005 | cb17690fe2db | paragraph | Implement all features through continuous Dev↔QA loops. Every task is validated before the next begins. This is where the bulk of the work happens — and where N |
| U006 | 12f4e3475171 | heading | ## Pre-Conditions |
| U007 | e30800bd5c6c | list | - [ ] Phase 2 Quality Gate passed (foundation verified) - [ ] Sprint Prioritizer backlog available with RICE scores - [ ] CI/CD pipeline operational - [ ] Desig |
| U008 | 027bb74959b8 | heading | ## The Dev↔QA Loop — Core Mechanic |
| U009 | 43b14bf5f4e0 | paragraph | The Agents Orchestrator manages every task through this cycle: |
| U010 | 3900cae98a37 | code | ``` FOR EACH task IN sprint_backlog (ordered by RICE score): 1. ASSIGN task to appropriate Developer Agent (see assignment matrix) 2. Developer IMPLEMENTS task  |
| U011 | 285a81f02f4a | heading | ## Agent Assignment Matrix |
| U012 | d082d82a6557 | heading | ### Primary Developer Assignment |
| U013 | c9a4ead540a3 | paragraph | \| Task Category \| Primary Agent \| Backup Agent \| QA Agent \| \|--------------\|--------------\|-------------\|----------\| \| **React/Vue/Angular UI** \| Frontend Devel |
| U014 | ee64e1d69fef | heading | ### Specialist Support (activated as needed) |
| U015 | 39fd63f68e76 | paragraph | \| Specialist \| When to Activate \| Trigger \| \|-----------\|-----------------\|---------\| \| UI Designer \| Component needs visual refinement \| Developer requests des |
| U016 | 8430f217eaa5 | heading | ## Parallel Build Tracks |
| U017 | 3582cd18cc36 | paragraph | For NEXUS-Full deployments, four tracks run simultaneously: |
| U018 | e7bc7b8d9404 | heading | ### Track A: Core Product Development |
| U019 | cc39552adba1 | code | ``` Managed by: Agents Orchestrator (Dev↔QA loop) Agents: Frontend Developer, Backend Architect, AI Engineer, Mobile App Builder, Senior Developer QA: Evidence  |
| U020 | 159f756effd4 | heading | ### Track B: Growth & Marketing Preparation |
| U021 | c469a3bbe1c7 | code | ``` Managed by: Project Shepherd Agents: Growth Hacker, Content Creator, Social Media Strategist, App Store Optimizer Sprint cadence: Aligned with Track A miles |
| U022 | 0a303d6ebea7 | heading | ### Track C: Quality & Operations |
| U023 | 87e09b6cc17f | code | ``` Managed by: Agents Orchestrator Agents: Evidence Collector, API Tester, Performance Benchmarker, Workflow Optimizer, Experiment Tracker Continuous activitie |
| U024 | f46fa3d1d4fc | heading | ### Track D: Brand & Experience Polish |
| U025 | a85136f92d3c | code | ``` Managed by: Brand Guardian Agents: UI Designer, Brand Guardian, Visual Storyteller, Whimsy Injector Triggered activities: - UI Designer → Component refineme |
| U026 | b348e95c7863 | heading | ## Sprint Execution Template |
| U027 | 28b393b0f8e5 | heading | ### Sprint Planning (Day 1) |
| U028 | d612566f7572 | code | ``` Sprint Prioritizer activates: 1. Review backlog with updated RICE scores 2. Select tasks for sprint based on team velocity 3. Assign tasks to developer agen |
| U029 | 7a294f96149b | heading | ### Daily Execution (Day 2 to Day N-1) |
| U030 | 190302e7a820 | code | ``` Agents Orchestrator manages: 1. Current task status check 2. Dev↔QA loop execution 3. Blocker identification and resolution 4. Progress tracking and reporti |
| U031 | 91ab3c72eb8d | heading | ### Sprint Review (Day N) |
| U032 | 967eb05ff4f2 | code | ``` Project Shepherd facilitates: 1. Demo completed features 2. Review QA evidence for each task 3. Collect stakeholder feedback 4. Update backlog based on lear |
| U033 | af0847ceae2f | heading | ### Sprint Retrospective |
| U034 | 1c09e7312f3e | code | ``` Workflow Optimizer facilitates: 1. What went well? 2. What could improve? 3. What will we change next sprint? 4. Process efficiency metrics Output: Retrospe |
| U035 | f5272b7211b6 | heading | ## Orchestrator Decision Logic |
| U036 | 221b927ecc10 | heading | ### Task Failure Handling |
| U037 | 61e3b8271e7c | code | ``` WHEN task fails QA: IF attempt == 1: → Send specific QA feedback to developer → Developer fixes ONLY the identified issues → Re-submit for QA IF attempt ==  |
| U038 | 4374fab9563b | heading | ### Parallel Task Management |
| U039 | 21912502dcfe | code | ``` WHEN multiple tasks have no dependencies: → Assign to different developer agents simultaneously → Each runs independent Dev↔QA loop → Orchestrator tracks al |
| U040 | 2ff125171ea8 | heading | ## Quality Gate Checklist |
| U041 | a7210c854e04 | paragraph | \| # \| Criterion \| Evidence Source \| Status \| \|---\|-----------\|----------------\|--------\| \| 1 \| All sprint tasks pass QA (100% completion) \| Evidence Collector s |
| U042 | c0b894b37cd1 | heading | ## Gate Decision |
| U043 | 8bccb0ebeb73 | paragraph | **Gate Keeper**: Agents Orchestrator |
| U044 | f869c3bf3be5 | list | - **PASS**: Feature-complete application → Phase 4 activation - **CONTINUE**: More sprints needed → Continue Phase 3 - **ESCALATE**: Systemic issues → Studio Pr |
| U045 | b553ae496697 | heading | ## Handoff to Phase 4 |
| U046 | 5f551bfc9cdb | code | ```markdown ## Phase 3 → Phase 4 Handoff Package ### For Reality Checker: - Complete application (all features implemented) - All QA evidence from Dev↔QA loops  |
| U047 | 58b63e273b96 | paragraph | --- |
| U048 | 6bf2dba9bc9c | paragraph | *Phase 3 is complete when all sprint tasks pass QA, all API endpoints are validated, performance baselines are met, and no critical bugs remain open.* |
