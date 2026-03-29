"""
LangGraph node functions – one per NEXUS phase, plus the quality gate.

Each phase node:
  1. Asks the supervisor to plan the phase
  2. Executes each planned task via the assigned Ollama model
  3. Collects results into state
"""

from __future__ import annotations

import logging
from typing import Any

from .agents import AgentSpec, agents_for_phase, load_all_agents
from .config import PipelineConfig
from .models import call_model
from .state import AgentResult, PipelineState
from .supervisor import plan_phase, quality_gate, select_model_for_task

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared execution helpers
# ---------------------------------------------------------------------------

def _execute_phase(
    state: PipelineState,
    phase: str,
    config: PipelineConfig,
) -> dict[str, Any]:
    """
    Generic phase executor:
      1. Load agents for the phase
      2. Ask supervisor to plan
      3. Execute each task against the chosen Ollama model
      4. Return state updates
    """
    registry = load_all_agents(state["repo_root"])
    available = agents_for_phase(phase, registry)

    if not available:
        msg = f"⚠ Phase '{phase}': no agents found in registry – skipping."
        log.warning(msg)
        return {
            "messages": [msg],
            "current_phase": phase,
        }

    # --- Supervisor plans the phase ---
    log.info(f"\n{'='*60}")
    log.info(f"  PHASE: {phase.upper()}")
    log.info(f"  Agents available: {[a.name for a in available]}")
    log.info(f"{'='*60}")

    plan = plan_phase(state, phase, available, config)
    results: list[AgentResult] = []
    messages: list[str] = [f"▶ Phase {phase} — {len(plan)} tasks planned by supervisor"]

    # --- Execute each task ---
    for task_def in plan:
        agent_name = task_def.get("agent", "Unknown")
        task_desc = task_def.get("task", "")
        rec_tier = task_def.get("recommended_tier", "free_fast")

        # Resolve agent spec
        agent_spec = registry.get(agent_name)
        if not agent_spec:
            messages.append(f"  ⚠ Agent '{agent_name}' not in registry – skipped")
            continue

        # Pick model
        model_spec = select_model_for_task(agent_name, rec_tier, config)

        # Build prompts
        system_prompt = (
            f"You are the {agent_spec.name} agent.\n"
            f"Division: {agent_spec.division}\n"
            f"Vibe: {agent_spec.vibe}\n\n"
            f"{agent_spec.system_prompt}\n\n"
            f"---\n"
            f"You are working in the **{phase.upper()}** phase of a development pipeline.\n"
            f"Be concise and produce actionable output."
        )

        user_prompt = (
            f"PROJECT BRIEF:\n{state['project_brief']}\n\n"
            f"YOUR TASK:\n{task_desc}\n\n"
            f"Produce your deliverable now.  Be specific and concise."
        )

        # Call the model (with retry)
        attempt = 0
        status = "failed"
        output = ""
        while attempt < config.max_retries:
            attempt += 1
            try:
                output = call_model(model_spec, system_prompt, user_prompt, config)
                status = "success"
                break
            except Exception as exc:
                log.warning(f"  ✗ {agent_name} attempt {attempt} failed: {exc}")
                output = str(exc)
                status = "retry" if attempt < config.max_retries else "failed"

        result = AgentResult(
            agent_name=agent_name,
            model_used=model_spec.name,
            model_tier=model_spec.tier.value,
            phase=phase,
            task_type=task_desc[:80],
            output=output,
            status=status,
            attempt=attempt,
        )
        results.append(result)

        status_icon = "✓" if status == "success" else "✗"
        messages.append(
            f"  {status_icon} {agent_name} → {model_spec.name} "
            f"({model_spec.tier.value}) [{status}]"
        )
        log.info(messages[-1])

    return {
        "results": results,
        "messages": messages,
        "current_phase": phase,
    }


# ---------------------------------------------------------------------------
# Quality gate node
# ---------------------------------------------------------------------------

def _gate_node(state: PipelineState, phase: str, config: PipelineConfig) -> dict[str, Any]:
    """Run the supervisor quality gate for a phase."""
    verdict = quality_gate(state, phase, config)
    icon = "✅" if verdict["passed"] else "❌"
    msg = f"{icon} Gate [{phase}]: {'PASSED' if verdict['passed'] else 'FAILED'} — {verdict['reason']}"
    log.info(msg)
    return {
        "gate_verdicts": [verdict],
        "messages": [msg],
        "should_halt": not verdict["passed"],
    }


# ---------------------------------------------------------------------------
# Phase node factories  (called by graph.py to bind config)
# ---------------------------------------------------------------------------

def make_phase_node(phase: str, config: PipelineConfig):
    """Return a LangGraph node function for the given phase."""
    def node(state: PipelineState) -> dict[str, Any]:
        return _execute_phase(state, phase, config)
    node.__name__ = f"phase_{phase}"
    return node


def make_gate_node(phase: str, config: PipelineConfig):
    """Return a LangGraph node function for the quality gate after *phase*."""
    def node(state: PipelineState) -> dict[str, Any]:
        return _gate_node(state, phase, config)
    node.__name__ = f"gate_{phase}"
    return node
