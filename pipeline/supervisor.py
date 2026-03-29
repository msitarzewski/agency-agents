"""
Claude Opus supervisor – the brain of the pipeline.

Responsibilities:
  1. Plan which agents to activate for a phase and what each should do
  2. Pick the best (cheapest viable) Ollama model for each agent task
  3. Issue quality-gate verdicts between phases
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .agents import AgentSpec, agents_for_phase
from .config import (
    AGENT_TASK_TYPE,
    TASK_STRENGTH_MAP,
    ModelSpec,
    ModelTier,
    PipelineConfig,
)
from .models import call_model, get_supervisor_model, pick_model
from .state import AgentResult, GateVerdict, PipelineState

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for the supervisor
# ---------------------------------------------------------------------------

SUPERVISOR_SYSTEM = """\
You are the **NEXUS Supervisor**, the autonomous orchestrator of a multi-agent
AI development pipeline.  You are Claude Opus — the most capable model in
the pipeline — and your job is to *direct*, not to *do*.

## Your responsibilities
1. **Phase planning** – Given a project brief, the current phase, and the
   available agents, produce a concrete plan: which agents to activate, what
   task each should perform, and in what order (or which can run in parallel).
2. **Model routing** – For every agent task, recommend the cheapest Ollama
   model tier that can handle the job.  Only escalate to heavier models when
   the task genuinely requires deeper reasoning or larger context.
3. **Quality gating** – After a phase completes, review the collected outputs
   and decide whether the phase passes.  Be evidence-based: require concrete
   artefacts, not vague assertions.

## Model tiers available (cheapest first)
- **free_fast**: qwen2.5:7b, llama3.1:8b, gemma2:9b, phi3:mini, deepseek-coder-v2:16b
- **free_medium**: qwen2.5:32b, llama3.1:70b
- **free_heavy**: deepseek-coder-v2:236b, mixtral:8x22b

Always prefer free_fast.  Use free_medium only for complex architecture,
security, or deep analysis.  Use free_heavy only as a last resort.

## Output format
Always respond with **valid JSON** (no markdown fences, no commentary).
"""


# ---------------------------------------------------------------------------
# Plan a phase
# ---------------------------------------------------------------------------

def plan_phase(
    state: PipelineState,
    phase: str,
    available_agents: list[AgentSpec],
    config: PipelineConfig,
) -> list[dict[str, Any]]:
    """
    Ask the supervisor to plan the work for *phase*.
    Returns a list of task dicts:
        [{"agent": "...", "task": "...", "recommended_tier": "free_fast"}, ...]
    """
    supervisor_model = get_supervisor_model(config.models)

    agent_summaries = "\n".join(
        f"- **{a.name}** ({a.division}): {a.description}"
        for a in available_agents
    )

    # Include prior phase outputs as context
    prior = [r for r in state.get("results", []) if r.get("status") == "success"]
    prior_summary = "\n".join(
        f"- [{r['agent_name']}] {r['output'][:200]}..."
        for r in prior[-10:]  # last 10 results for context window economy
    ) or "(no prior outputs)"

    prompt = f"""\
PROJECT BRIEF:
{state["project_brief"]}

CURRENT PHASE: {phase}

AVAILABLE AGENTS FOR THIS PHASE:
{agent_summaries}

PRIOR PHASE OUTPUTS (summary):
{prior_summary}

Produce a JSON array of tasks for this phase.  Each element:
{{
  "agent": "<agent name>",
  "task": "<specific instruction for this agent>",
  "recommended_tier": "free_fast" | "free_medium" | "free_heavy",
  "parallel_group": <int>   // tasks with the same group number can run in parallel
}}

Prioritise free_fast models.  Only escalate when the task genuinely requires it.
Return ONLY the JSON array."""

    raw = call_model(supervisor_model, SUPERVISOR_SYSTEM, prompt, config, max_tokens=4096)

    # Parse – strip markdown fences if the model wraps them
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Supervisor returned non-JSON plan, falling back to simple plan")
        plan = [
            {"agent": a.name, "task": f"Perform your core function for the {phase} phase.",
             "recommended_tier": "free_fast", "parallel_group": 0}
            for a in available_agents
        ]
    return plan


# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------

def quality_gate(
    state: PipelineState,
    phase: str,
    config: PipelineConfig,
) -> GateVerdict:
    """
    Ask the supervisor to review all results for *phase* and issue a verdict.
    """
    supervisor_model = get_supervisor_model(config.models)

    phase_results = [r for r in state.get("results", []) if r.get("phase") == phase]
    results_text = "\n\n".join(
        f"### {r['agent_name']} (model: {r['model_used']}, status: {r['status']})\n{r['output'][:500]}"
        for r in phase_results
    ) or "(no results)"

    prompt = f"""\
PHASE: {phase}
PROJECT BRIEF: {state["project_brief"][:500]}

PHASE RESULTS:
{results_text}

Review these results and decide whether the phase passes the quality gate.
Reply with a JSON object:
{{
  "passed": true | false,
  "reason": "<1-2 sentence explanation>"
}}
Return ONLY the JSON object."""

    raw = call_model(supervisor_model, SUPERVISOR_SYSTEM, prompt, config, max_tokens=512)
    raw = raw.strip().strip("`").strip()
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError:
        verdict = {"passed": True, "reason": "Supervisor response unparseable; defaulting to pass."}

    return GateVerdict(
        phase=phase,
        passed=verdict.get("passed", True),
        reason=verdict.get("reason", ""),
        reviewed_by=supervisor_model.name,
    )


# ---------------------------------------------------------------------------
# Model selection (supervisor-informed)
# ---------------------------------------------------------------------------

def select_model_for_task(
    agent_name: str,
    recommended_tier: str,
    config: PipelineConfig,
) -> ModelSpec:
    """
    Resolve the supervisor's tier recommendation to a concrete ModelSpec.
    Picks the best-fit model within that tier based on task-type strengths.
    """
    tier_map = {t.value: t for t in ModelTier}
    max_tier = tier_map.get(recommended_tier, ModelTier.FREE_FAST)

    task_type = AGENT_TASK_TYPE.get(agent_name, "general")

    return pick_model(
        task_type,
        TASK_STRENGTH_MAP,
        config.models,
        max_tier=max_tier,
    )
