"""
LangGraph graph construction – wires phases and quality gates into a
linear state machine with conditional halts.

Pipeline topology:

  START
    │
    ▼
  discover ─► gate_discover ─┐
                              │ (if passed)
  strategize ◄────────────────┘
    │
  gate_strategize ─┐
                    │
  scaffold ◄────────┘
    │
  gate_scaffold ─┐
                  │
  build ◄─────────┘
    │
  gate_build ─┐
               │
  harden ◄─────┘
    │
  gate_harden ─┐
                │
  launch ◄──────┘
    │
  gate_launch ─┐
                │
  operate ◄─────┘
    │
  gate_operate ─► END

If any gate fails, the pipeline halts.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .agents import list_phases
from .config import PipelineConfig
from .nodes import make_gate_node, make_phase_node
from .state import PipelineState


def build_graph(config: PipelineConfig) -> StateGraph:
    """
    Construct and compile the full NEXUS pipeline graph.
    """
    phases = list_phases()  # [discover, strategize, scaffold, build, harden, launch, operate]
    graph = StateGraph(PipelineState)

    # --- Add phase + gate nodes ---
    for phase in phases:
        graph.add_node(f"phase_{phase}", make_phase_node(phase, config))
        graph.add_node(f"gate_{phase}", make_gate_node(phase, config))

    # --- Halt node (reached when a gate fails) ---
    def halt_node(state: PipelineState) -> dict:
        return {"messages": ["🛑 Pipeline halted — quality gate failed."]}
    graph.add_node("halt", halt_node)

    # --- Edges ---
    # START → first phase
    graph.add_edge(START, f"phase_{phases[0]}")

    for i, phase in enumerate(phases):
        # phase → its gate
        graph.add_edge(f"phase_{phase}", f"gate_{phase}")

        # gate → next phase  OR  halt
        if i < len(phases) - 1:
            next_phase = phases[i + 1]
            graph.add_conditional_edges(
                f"gate_{phase}",
                _gate_router(next_phase),
                {
                    "continue": f"phase_{next_phase}",
                    "halt": "halt",
                },
            )
        else:
            # Final gate → END or halt
            graph.add_conditional_edges(
                f"gate_{phase}",
                _gate_router(None),
                {
                    "continue": END,
                    "halt": "halt",
                },
            )

    # halt → END
    graph.add_edge("halt", END)

    return graph.compile()


def _gate_router(next_phase: str | None):
    """Return a routing function that checks should_halt."""
    def router(state: PipelineState) -> str:
        if state.get("should_halt"):
            return "halt"
        return "continue"
    return router
