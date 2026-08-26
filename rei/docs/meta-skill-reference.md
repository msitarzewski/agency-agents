# Meta Skill Reference

Extended methodology, schemas, Parts B-H, anti-patterns, output modes, and validation checklists. Load on demand when building or deeply auditing components; not for routine invocations.

Canonical active auditor: `.cursor/skills/meta-skill/SKILL.md`.

---

# Full Cursor System Model

## Layer Responsibilities

### Rules

Persistent repo/team/user instructions loaded by Cursor to shape default behavior.

Use rules for:

- repo conventions
- architecture constraints
- coding style
- mandatory commands
- security constraints
- framework-specific standards
- canonical file references

Rules should be short, stable, and broadly applicable.

### Agents

Primary workers that interpret user intent, plan work, edit files, run tools, and coordinate execution.

Agents should orchestrate. They should not duplicate detailed skill logic.

### Subagents

Specialized workers with narrow roles, boundaries, and task-specific execution focus.

Use subagents for:

- architecture review
- implementation
- QA/testing
- code review
- UI/design review
- security review
- prompt/workflow review
- debugging investigation

Subagents should have:

- clear scope
- trigger conditions
- allowed actions
- skills they should use
- output format
- escalation rules

### Skills

Reusable capabilities and workflows.

Use skills for:

- detailed methodology
- repeatable playbooks
- domain expertise
- validation procedures
- scripts or supporting assets

Skills should be modular, callable, and reusable by multiple agents/subagents.

### Commands

Manual slash-command entry points.

Use commands for:

- frequently repeated workflows
- explicit task launchers
- mode selection
- routing to specific agents/subagents/skills

Commands should be short wrappers that invoke the right worker and workflow.

### MCP

External tool/data integration layer.

Use MCP for:

- external systems
- APIs
- databases
- SaaS tools
- docs/search systems
- workflow automation

MCP should expose capabilities. Prompting logic belongs in rules, skills, agents, or commands.

### Hooks

Event-triggered automation and guardrails.

Use hooks for:

- pre-run checks
- post-edit validation
- formatting
- lint/test triggers
- policy enforcement
- audit logging
- safety checks

Hooks should be deterministic, fast, and safe.

### Plugins

Packaging and distribution layer.

Use plugins to bundle:

- rules
- agents/subagents
- skills
- commands
- MCP configuration
- hooks
- documentation

A plugin should represent a coherent capability package, not a random collection of files.

---

# Architecture Decision Matrix

| Need | Put it in |
|---|---|
| Always-on repo standard | Rule |
| Specialized AI role | Subagent |
| Main execution behavior | Agent |
| Reusable workflow/playbook | Skill |
| Manual shortcut | Command |
| External tool/data access | MCP |
| Event-triggered automation | Hook |
| Shareable bundled capability | Plugin |

## Placement Rules

- If it must always influence behavior, use a rule.
- If it is a reusable workflow, use a skill.
- If it is a specialized worker role, use a subagent.
- If it is a manual entry point, use a command.
- If it connects to an external system, use MCP.
- If it runs automatically on events, use a hook.
- If it should be installed/reused as a package, use a plugin.
- If two layers contain the same logic, keep the logic in the lower-reuse layer only when it is genuinely context-specific.

## Central Operating Model

Rules define persistent defaults.  
Agents orchestrate execution.  
Subagents specialize execution.  
Skills contain reusable methodology.  
Commands trigger workflows.  
MCP exposes external capabilities.  
Hooks enforce deterministic automation.  
Plugins package the system.

---

# Standard Schemas

## Standard Rule Schema

Every rule should define:

1. Purpose
2. Scope
3. When It Applies
4. Required Behavior
5. Forbidden Behavior
6. Examples or References, only if useful
7. Validation Commands, if relevant

Rules should be concise. Avoid long workflows inside rules.

## Standard Skill Schema

Every generated or revised skill should use:

1. Description (mandatory; quality standard above)
2. Purpose
3. When To Use
4. Required Context
5. Workflow
6. Expected Deliverable
7. Safeguards

Optional only when useful:

- Examples
- Edge Cases
- Validation
- Tooling Notes
- Inputs
- Outputs
- Dependencies

## Standard Agent Schema

Every generated or revised agent should clearly define:

1. Description (mandatory; quality standard above)
2. Purpose
3. Scope
4. Trigger Conditions
5. Decision Logic
6. Skills It Should Use
7. Escalation Rules
8. Output Style
9. Safeguards

Optional only when useful:

- Tool Access
- Boundaries
- Retry Logic
- Failure Handling
- Handoff Rules

## Standard Subagent Schema

Every subagent should define:

1. Description (mandatory; quality standard above)
2. Purpose
3. Scope
4. Trigger Conditions
5. Responsibilities
6. Skills It Should Use
7. Tools/MCP Access
8. Commands That May Invoke It
9. Output Format
10. Boundaries
11. Escalation Rules
12. Safeguards

Subagents should specialize. Avoid broad "do everything" agents.

## Standard Command Schema

Every command should define:

1. Description (mandatory; quality standard above)
2. Purpose
3. Invocation Context
4. Target Agent/Subagent
5. Skills To Use
6. Inputs Expected
7. Execution Instructions
8. Output Format
9. Edit Permissions
10. Stop Conditions

Commands should be thin wrappers, not full duplicated workflows.

## Standard MCP Schema

Every MCP integration should define:

1. Purpose
2. External System
3. Available Capabilities
4. Data Access Scope
5. Security Boundaries
6. Authentication Assumptions
7. When To Use
8. When Not To Use
9. Failure Handling
10. Audit/Logging Needs

MCP should expose capability. Prompting logic belongs in rules, skills, agents, or commands.

## Standard Hook Schema

Every hook should define:

1. Purpose
2. Trigger Event
3. Action Performed
4. Allowed Side Effects
5. Failure Behavior
6. Safety Limits
7. Logging
8. Disable/Bypass Policy

Hooks should be deterministic, fast, and safe.

## Standard Plugin Schema

Every plugin should define:

1. Description (recommended; quality standard above)
2. Purpose
3. Target User
4. Included Components
5. Component Map
6. Installation Assumptions
7. Usage Commands
8. MCP Requirements
9. Hook Behavior
10. Governance
11. Validation Checklist
12. Version / Status
13. Maintenance Notes

---

# PART A — Component Classifier

## Purpose

Classify a request, prompt, workflow, or configuration element into the correct Cursor layer.

## Workflow

1. Identify the user's real goal.
2. Identify whether the need is persistent, reusable, manual, specialized, external, event-triggered, or package-level.
3. Assign the correct layer:
   - Rule
   - Skill
   - Agent
   - Subagent
   - Command
   - MCP
   - Hook
   - Plugin
4. Detect overlap with existing components.
5. Recommend create/update/delete/merge.
6. Provide target file path and minimal file contents when useful.

## Deliverable

Return:

1. Classification
2. Reasoning
3. Recommended layer
4. Components to add/change/remove
5. Proposed file path
6. Draft content if requested

---

# PART B — Skill Builder

## Step 1: Identify Core Capability

Determine the real capability requested.

Name by capability, not vague branding.

Prefer:

- review-diff
- debug-issue
- plan-feature

Avoid:

- helper
- genius-agent
- step2-flow

## Step 2: Define Scope

Determine what belongs inside the skill and what belongs elsewhere.

Split oversized skills.

## Step 3: Gather Minimum Required Context

Request only inputs needed for strong execution.

## Step 4: Build Deterministic Workflow

Use explicit, observable steps.

Avoid vague wording.

## Step 5: Define Deliverable

Specify immediately useful outputs.

## Step 6: Add Safeguards

Prevent common failure modes.

## Step 7: Optimize for Reusability

Prefer capability-based wording.

## Step 8: Optimize for Simplicity

Remove low-value complexity.

## Step 9: Align With Library

Keep consistency across skills.

## Step 10: Add Composition Logic

Define prerequisites, downstream skills, and handoffs when useful.

---

# PART C — Agent/Subagent Auditor

## Purpose

Ensure existing agents and subagents use the Cursor system correctly.

Review whether agents are orchestrating well instead of duplicating logic.

## Review Workflow

### Step 1: Identify Role

What is the agent/subagent supposed to do?

Examples:

- planning
- implementation
- debugging
- review
- triage
- research
- UI/design review
- security review

### Step 2: Detect Available Skills

List relevant skills the agent/subagent should likely use.

Example:

A review agent should likely use:

- review-diff
- branch-gate
- add-tests, if missing coverage is found

### Step 3: Check Skill Usage Correctness

Audit:

- Is the correct skill being used?
- Is it triggered at the right time?
- Is the skill skipped when it should run?
- Is wrong logic embedded in the agent instead?
- Is the agent duplicating skill instructions?
- Is skill order correct?
- Are handoffs clear?

### Step 4: Check Decision Quality

Audit:

- good task classification
- correct routing
- correct escalation
- no unnecessary questions
- no overreach
- no hidden assumptions

### Step 5: Check Output Quality

Audit:

- concise enough
- actionable
- complete enough
- aligned with user intent
- consistent tone
- proper deliverable format


### Step 6: Context Cost Audit

Audit:

- recurring context cost
- load frequency
- duplicated instructions
- oversized components
- unnecessary always-on content
- skills loaded too frequently
- reference material embedded inside agents

Recommend:

- move content to reference docs
- split oversized components
- reduce always-on context
- convert repeated workflows into skills
- convert manual workflows into commands
- scope rules more narrowly

### Step 7: Recommend Fixes

Return:

1. Critical issues
2. Skill misuse
3. Missing skills to invoke
4. Logic to remove from agent/subagent
5. Simpler architecture
6. Updated design

---

# PART D — Command Builder

## Purpose

Create or improve slash commands that reliably launch common workflows.

## Workflow

1. Identify the repeatable task.
2. Decide whether a command is justified.
3. Route the command to the correct agent/subagent.
4. Reference relevant skills instead of duplicating their full logic.
5. Define edit permissions.
6. Define output format.
7. Define stop conditions.
8. Keep command short and explicit.

## Command Design Rules

- Commands are entry points, not full systems.
- Commands should not duplicate complete skill logic.
- Commands should specify whether file edits are allowed.
- Commands should specify the intended worker.
- Commands should specify expected output.

---

# PART E — MCP Integration Reviewer

## Purpose

Decide whether an external integration should be implemented through MCP and define safe capability boundaries.

## Workflow

1. Identify the external system or data source.
2. Determine whether local context is enough.
3. Define required capabilities.
4. Define least-privilege data access.
5. Define authentication assumptions.
6. Define failure behavior.
7. Define usage boundaries.
8. Decide which agents/subagents/commands should be allowed to use it.
9. Document security and operational risks.

## MCP Fit Test

Use MCP when:

- the workflow needs external data or actions
- the integration will be reused
- the interface can be capability-based
- tool use improves accuracy or automation

Do not use MCP when:

- static repo context is enough
- a rule or skill is sufficient
- the integration adds security risk without clear value
- manual input is simpler and safer

---

# PART F — Hook Designer

## Purpose

Design deterministic hooks for automation, validation, and guardrails.

## Workflow

1. Identify the event trigger.
2. Define deterministic action.
3. Define allowed side effects.
4. Define failure behavior.
5. Define logging behavior.
6. Define bypass/disable policy.
7. Verify the hook is fast and safe.
8. Avoid subjective reasoning inside hooks.

## Hook Fit Test

Use hooks when:

- the action is deterministic
- the trigger is clear
- failure behavior can be specified
- automation prevents real mistakes

Do not use hooks when:

- the action requires nuanced judgment
- the action is slow or flaky
- the hook might block work without recovery
- the behavior is better handled by a command or skill

---

# PART G — Cursor Plugin Architect

## Purpose

Design full Cursor plugins that package rules, agents/subagents, skills, commands, MCP servers, hooks, and documentation into a coherent reusable development system.

## Plugin Design Workflow

### Step 1: Define Plugin Purpose

Identify the coherent capability the plugin provides.

Good plugin names:

- cursor-dev-system
- frontend-quality-system
- real-estate-automation-dev
- ghl-prompt-engineering-system
- testing-and-review-system

Avoid vague names:

- ai-helper
- agent-pack
- misc-tools

### Step 2: Define Target Users

Clarify who the plugin serves:

- solo developer
- internal team
- frontend team
- backend team
- automation engineer
- prompt engineer
- reviewer/QA team

### Step 3: Map Required Components

For each capability, decide whether it needs:

- rules
- agents/subagents
- skills
- commands
- MCP
- hooks
- docs

Do not create a component unless it has a clear job.

### Step 4: Design Component Boundaries

Prevent duplication:

- Rules define persistent standards.
- Agents orchestrate execution.
- Subagents define specialist behavior.
- Skills define reusable workflows.
- Commands invoke workflows.
- MCP exposes tools/data.
- Hooks enforce deterministic automation.
- Plugins package the system.

### Step 5: Define Invocation Flow

Specify how users interact with the plugin.

Example:

1. User types `/review-diff`
2. Command routes to code-review subagent
3. Subagent uses review-diff skill
4. Skill applies repo rules
5. Hook runs lint/test validation
6. MCP fetches external context if needed
7. Output returns findings and patch recommendations

### Step 6: Define File Layout

Produce an installable Cursor plugin layout.

Recommended structure:

```txt
.cursor-plugin/
  plugin.json
README.md
CHANGELOG.md
rules/
  repo-standards.mdc
skills/
  some-skill/
    SKILL.md
agents/
  some-subagent.md
commands/
  some-command.md
hooks/
  hooks.json
mcp.json
docs/
  operating-model.md
```

### Step 7: Define Governance

Every plugin should include:

- ownership
- status
- version
- intended scope
- install assumptions
- component inventory
- validation checklist
- deprecation policy
- change log

### Step 8: Validate Plugin Quality

Check:

1. Clear purpose
2. No duplicate logic
3. Correct component placement
4. Minimal always-on context
5. Strong manual commands
6. Useful subagent boundaries
7. Skills are reusable
8. MCP is justified
9. Hooks are safe and deterministic
10. Plugin is installable and maintainable

---

# PART H — Full Cursor Configuration Auditor

## Purpose

Audit an entire Cursor configuration across rules, agents, subagents, skills, commands, MCP, hooks, and plugins.

## Audit Workflow

### Step 1: Inventory

List all known components:

- rules
- agents
- subagents
- skills
- commands
- MCP servers
- hooks
- plugins

### Step 2: Classify Responsibilities

For each component, identify its actual role.

Flag:

- duplicated responsibilities
- vague purpose
- missing trigger
- bloated instructions
- unclear ownership

### Step 3: Detect Misplacement

Flag logic in the wrong layer:

- long workflows inside rules
- repeated skill logic inside agents
- commands that duplicate skills
- MCP used for prompt logic
- hooks used for subjective decisions
- subagents that are too broad
- plugins that are just file dumps

### Step 4: Analyze Execution Flow

Map common workflows:

- plan feature
- implement feature
- review diff
- fix tests
- debug issue
- audit UI
- release change

For each workflow, define:

1. command
2. agent/subagent
3. skills
4. rules applied
5. MCP used
6. hooks triggered
7. expected output

### Step 5: Identify Gaps

Find missing:

- commands for frequent workflows
- rules for persistent conventions
- skills for repeated methodology
- subagents for specialist work
- hooks for deterministic enforcement
- MCP for external tool access
- plugin packaging/docs

### Step 6: Context Cost Audit

Analyze:

1. Total always-on context
2. Frequently loaded components
3. Duplicated instructions
4. Oversized rules
5. Oversized agents
6. Skills that should be references
7. Reference content that is loaded unnecessarily

Return:

- high-cost components
- root causes
- recommended reductions
- estimated context savings

### Step 7: Recommend Target Architecture

Return:

1. Current-state diagnosis
2. Main issues
3. Context cost analysis
4. High-cost components
5. Recommended component map
6. Files to add/change/remove
7. Migration sequence
8. Validation plan
9. Estimated context reduction

---

# Anti-Patterns

## General Anti-Patterns

Flag these:

- Agent reimplements skill logic internally
- Agent ignores available skill
- Agent asks for info it could infer
- Agent overcomplicates simple tasks
- Agent too broad / unclear role
- Agent does planning and implementation poorly in one blob
- Agent outputs prose instead of deliverables
- Agent uses examples as core logic
- Agent duplicates other agents

## Rule Anti-Patterns

- Rules contain long workflows
- Rules duplicate skills
- Rules are too broad
- Rules are always-on when they should be conditional
- Rules include outdated conventions

## Skill Anti-Patterns

- Skill is just a vague prompt
- Skill duplicates another skill
- Skill mixes unrelated capabilities
- Skill lacks deliverable format
- Skill requires too much context

## Subagent Anti-Patterns

- Subagent is too broad
- Subagent duplicates the main agent
- Subagent embeds full skill logic
- Subagent has unclear edit permissions
- Subagent lacks escalation rules

## Command Anti-Patterns

- Command duplicates a full skill
- Command is too vague
- Command does not specify output
- Command does not specify whether edits are allowed
- Command does not route to the right subagent/skill

## MCP Anti-Patterns

- MCP is added without clear use case
- MCP exposes too much access
- MCP lacks failure handling
- MCP replaces simple local context unnecessarily
- MCP is used for policy instead of capability

## Hook Anti-Patterns

- Hook performs subjective reasoning
- Hook is slow or brittle
- Hook has unsafe side effects
- Hook blocks work without clear recovery
- Hook duplicates test/lint commands poorly

## Plugin Anti-Patterns

- Plugin bundles unrelated resources
- Plugin lacks README or operating model
- Plugin has no component map
- Plugin has no validation checklist
- Plugin duplicates project-local configuration without reason

---

# Example Policy

Use examples only when they materially improve execution.

Default: no examples.

Add examples only for:

- ambiguous outputs
- uncommon syntax
- edge cases
- contrastive good vs bad behavior
- error-prone tool usage

Rules:

- minimal
- generic
- non-dominant
- removable without harming the component

---

# Output Modes

## If Building a Full Cursor Plugin

Return:

1. Plugin purpose
2. Target user
3. Recommended architecture
4. Component map
5. File tree
6. Key file contents
7. Install/use instructions
8. Validation checklist
9. Maintenance notes

## If Auditing Full Cursor Configuration

Return:

1. Verdict
2. Component inventory
3. Misplaced logic
4. Duplications
5. Missing layers
6. Recommended target architecture
7. Prioritized changes
8. Migration plan

## If Reviewing a Rule

Return:

1. Verdict
2. Scope correctness
3. Trigger correctness
4. Bloat/duplication issues
5. Revised rule if requested

## If Reviewing a Skill

Return:

1. Verdict
2. Strengths
3. Gaps
4. Recommended changes
5. Revised version if requested

## If Reviewing an Agent

Return:

1. Verdict
2. Correct skill usage
3. Misused / missing skills
4. Logic flaws
5. Architecture improvements
6. Revised agent if requested

## If Reviewing a Subagent

Return:

1. Verdict
2. Role clarity
3. Boundary issues
4. Correct skill usage
5. Command/MCP/hook interactions
6. Revised subagent if requested

## If Reviewing a Command

Return:

1. Verdict
2. Invocation clarity
3. Routing correctness
4. Skill/subagent usage
5. Output quality
6. Revised command if requested

## If Reviewing MCP

Return:

1. Verdict
2. Capability fit
3. Access/security concerns
4. Failure handling
5. Whether MCP is actually needed

## If Reviewing a Hook

Return:

1. Verdict
2. Trigger correctness
3. Safety
4. Determinism
5. Failure behavior
6. Revised hook if requested

---

# Validation Checklist

Before finalizing, verify:

## Full Stack Checks

1. Clear system purpose
2. All discoverable components include clear descriptions
3. Description quality standard is met (verb + outcome + scope, no vague wording)
4. Correct component placement
5. Minimal always-on context
6. No duplicated logic
7. Commands route correctly
8. Subagents specialize correctly
9. Skills are reusable
10. Rules are concise
11. MCP is justified and bounded
12. Hooks are deterministic and safe
13. Plugin packaging is coherent
14. Documentation is sufficient

## Rule Checks

1. Clear purpose
2. Correct scope
3. Correct trigger/application
4. Concise
5. No skill duplication
6. Practical enforcement value

## Skill Checks

1. Clear purpose
2. Description is present and quality-compliant
3. Correct triggers
4. Minimal context
5. Deterministic workflow
6. Useful deliverable
7. Practical safeguards
8. Reusable
9. Consistent
10. Examples only when needed
11. Concise

## Agent/Subagent Checks

1. Clear role
2. Description is present and quality-compliant
3. Correct boundaries
4. Uses right skills
5. Correct sequencing
6. No duplicated logic
7. Good decisions
8. Good outputs
9. Escalates correctly
10. Consistent behavior
11. Practical value

## Command Checks

1. Clear purpose
2. Description is present and quality-compliant
3. Correct routing
4. References skills without duplicating them
5. Defines edit permissions
6. Defines output format
7. Useful as a repeatable shortcut

## MCP Checks

1. Clear external capability
2. Least-privilege access
3. Authentication assumptions documented
4. Failure behavior defined
5. Agents/commands allowed to use it are clear

## Hook Checks

1. Clear trigger
2. Deterministic action
3. Safe side effects
4. Fast enough
5. Failure behavior defined
6. Bypass policy defined

## Plugin Checks

1. Clear purpose
2. Coherent file tree
3. Manifest present
4. Component inventory documented
5. Usage commands documented
6. Validation plan present
7. Maintenance policy present

## Context Cost Checks

1. Load frequency is explicitly defined.
2. Always-on content is minimized.
3. No duplicated instructions across layers.
4. Long examples are stored as reference material.
5. Skills are loaded only when relevant.
6. Agents orchestrate rather than contain methodology.
7. Rules contain standards, not workflows.
8. Context-heavy content is not auto-loaded.
9. The component has an acceptable token footprint.
---

# Outcome Check

Will this improve:

- speed
- quality
- reliability
- consistency
- maintainability
- delegation quality
- handoff clarity
- decision quality
- governance
- plugin portability

If not, revise.

---

# Lifecycle Rules

Classify when useful:

- active
- experimental
- superseded
- deprecated

Prefer improving existing systems over creating duplicates.

---

# Decision Priorities

Rank options by:

1. Practical value
2. Speed to usefulness
3. Simplicity
4. Reliability
5. Reuse
6. Scale

---

# Context Budget Guidelines

Target sizes:

| Component | Recommended Size |
|------------|------------|
| Global Rule | 100-300 words |
| Scoped Rule | 200-600 words |
| Frequently Used Agent | 300-800 words |
| Specialized Agent | 500-1500 words |
| Skill | 600-2000 words |
| Command | 50-300 words |
| Reference Document | No practical limit |

These are optimization guidelines, not hard limits.

Larger components require explicit justification.

---

# Final Rule

Treat the Cursor AI configuration stack like a production system:

- intentionally designed
- critically reviewed
- tested in real workflows
- improved over time
- kept clean
- governed as code
