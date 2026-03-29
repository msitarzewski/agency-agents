"""
LangGraph state definition for the NEXUS dev pipeline.

The state flows through 7 phases.  Each phase appends its results
to the shared state so downstream phases have full context.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, TypedDict


# ---------------------------------------------------------------------------
# Atomic artefact produced by a single agent invocation
# ---------------------------------------------------------------------------

class AgentResult(TypedDict, total=False):
    agent_name: str
    model_used: str
    model_tier: str
    phase: str
    task_type: str
    output: str
    status: Literal["success", "retry", "failed"]
    attempt: int


# ---------------------------------------------------------------------------
# Quality-gate verdict
# ---------------------------------------------------------------------------

class GateVerdict(TypedDict, total=False):
    phase: str
    passed: bool
    reason: str
    reviewed_by: str  # model that issued the verdict


# ---------------------------------------------------------------------------
# Pipeline state – shared across all LangGraph nodes
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    # --- Inputs (set once at start) ---
    project_brief: str                                    # user's project description
    repo_root: str                                        # path to DreamEngine repo

    # --- Accumulating outputs (reducer = list concat) ---
    results: Annotated[list[AgentResult], operator.add]
    gate_verdicts: Annotated[list[GateVerdict], operator.add]
    messages: Annotated[list[str], operator.add]          # human-readable log

    # --- Supervisor routing state ---
    current_phase: str
    next_phase: str
    phase_plan: list[dict[str, Any]]                      # supervisor's plan for current phase

    # --- Control ---
    retry_count: int
    should_halt: bool
