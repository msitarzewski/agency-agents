---
name: research-goal
description: Goal-driven finance research workflow: attach a research-only objective, track criteria, and add evidence while avoiding live trading execution.
category: flow
---

# Goal-Driven Finance Research

Use this skill when a user asks for a multi-step finance research task, comparison, audit, thesis review, or "keep working until the answer is supported." The goal runtime is for research only. Never use it to place, submit, or execute trades.

## When to Attach a Goal

Start a goal when the task has any of these traits:

- It needs multiple criteria before a conclusion is credible.
- It compares strategies, assets, regimes, or evidence sources.
- It may continue across turns or require a final audit.
- The user asks for "long driven task", "goal", "审计", "对比", "研究结论", or similar.

Do not start a goal for a tiny one-shot answer unless the user explicitly asks.

## Tool Flow

1. Call `start_research_goal` with a concise research-only objective.
2. Include 3-5 acceptance criteria when the user provided enough context.
3. Before continuing an existing task, call `get_research_goal`.
4. After a market-data lookup, backtest, document read, web source, or manual reasoning step, call `add_goal_evidence`.
5. Link evidence to a criterion using `criterion_id` or `criterion_index`.
6. When all required criteria have been audited, call `update_research_goal_status`.

## Criteria Template

Use this shape when the user did not provide criteria:

- Define the research-only thesis and symbol universe.
- Collect fresh market, benchmark, or artifact evidence.
- Compare alternatives or a control baseline.
- Record caveats, contradictions, and the non-advice boundary.

## Evidence Rules

- Keep evidence short and concrete.
- Prefer artifact-backed evidence when a tool produced a run or file.
- Include `run_id`, `artifact_path`, `source_provider`, `source_type`, `symbol_universe`, `benchmark`, and `data_as_of` when known.
- `tool_call_id` is traceability only. Completion needs verified evidence from an existing `run_id` or an allowed `artifact_path` with a matching sha256 hash.
- Do not mark live trading instructions as evidence. Refuse or reframe them as research-only analysis.

## Completion Rules

- Use `update_research_goal_status(status="complete")` only after every required criterion has an audit row.
- Satisfied audit rows must cite verified `evidence_ids`.
- Use `status="blocked"` or `status="insufficient_evidence"` when evidence is missing, stale, contradictory, or not verifiable.
- Use `status="cancelled"` only when the user explicitly asks to end or discard the goal.

## Response Style

Tell the user what the goal is tracking only when it helps. Do not flood the answer with ledger details. Lead with the research conclusion, then mention which criteria remain unresolved.
