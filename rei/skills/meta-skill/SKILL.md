---
name: meta-skill
description: SKL - Audit and govern Cursor AI configuration (rules, agents, skills, commands, MCP, hooks, plugins) for architecture and token efficiency.
status: active
owner: user
---

# Meta Skill (active auditor)

## Naming & descriptions

- Prefixes: `CMD -`, `AGENT -`, `SKL -` (plain text, no brackets).
- Every discoverable component: one sentence, action verb, outcome + scope; avoid vague "helper/misc" wording.

## Purpose

Design, audit, and refactor Cursor configuration stacks—rules through plugins—for execution quality, governance, and **minimal recurring context cost**.

## When to use

Full-system or layer-specific work: rules, skills, agents/subagents, commands, MCP, hooks, plugins, token-efficiency audits, plugin packaging. Inputs may be incomplete.

## Core principles

Clarity, reuse, concise wording, correct layer placement, preserve what works, keep always-on context small. Configuration is production infrastructure.

## Token budget governance

Classify each component: **Always-On** | **Frequently Loaded** | **Occasionally Loaded** | **Reference Only**.

**Design rules:** Always-on = extremely concise. Frequent = orchestrate, don't teach. Long examples/schemas → reference docs. Avoid unjustified "always read/load." Route; don't embed. Minimize cross-layer duplication.

**Required review (every change):** load frequency, invocation rate, context cost, duplication risk, reference-doc candidacy.

## PART A — Component classifier

1. Identify real goal and persistence (persistent / reusable / manual / specialized / external / event / package).
2. Assign layer: Rule, Skill, Agent, Subagent, Command, MCP, Hook, Plugin.
3. Detect overlap with existing components.
4. Recommend create / update / delete / merge / split / scope / convert-to-reference.
5. Deliver: classification, reasoning, layer, file changes, optional draft content.

## Full configuration audit (summary)

For holistic audits (`/audit-cursor-config`, `/audit-token-efficiency`):

1. Inventory all components.
2. Classify purpose, load frequency, token risk, duplication/misplacement.
3. Map execution flows (plan → implement → test → review).
4. Identify gaps and high-cost components.
5. Recommend target architecture, migration sequence, validation, estimated savings.

**Extended playbooks** (Parts B–H builders, standard schemas, anti-patterns, output modes, checklists, context budget tables): **`.cursor/docs/meta-skill-reference.md`** — load on demand when building or deeply revising components.

## Outcome check

Revise if the change does not improve speed, quality, reliability, consistency, maintainability, delegation, or governance.

## Final rule

Treat the Cursor stack like governed code: intentional design, critical review, real-workflow validation, continuous cleanup.
