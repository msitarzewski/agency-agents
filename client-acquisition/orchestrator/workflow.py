"""Phase 1/2 lead workflow orchestration.

Agent execution is intentionally injected as a callable. This keeps the core
workflow independent of a particular LLM provider or agent runtime.
"""

from dataclasses import asdict
from typing import Any, Callable, Dict

from .models import AgentRun, Lead, LeadStatus, RunStatus, utc_now
from .state_machine import transition

AgentExecutor = Callable[[str, Dict[str, Any]], Dict[str, Any]]


class WorkflowError(RuntimeError):
    """Raised when an agent step cannot complete safely."""


def run_step(
    lead: Lead,
    capability: str,
    executor: AgentExecutor,
    context: Dict[str, Any],
) -> AgentRun:
    """Execute one agent step while preserving the workflow trace ID."""
    trace_id = context.get("trace_id")
    run = AgentRun(agent=capability, lead_id=lead.id, input=context)
    if trace_id:
        run.trace_id = str(trace_id)
    run.status = RunStatus.RUNNING
    run.started_at = utc_now()

    try:
        result = executor(capability, context)
        if not isinstance(result, dict):
            raise TypeError("Agent executor must return a dictionary")
        run.output = result
        run.status = RunStatus.SUCCEEDED
        return run
    except Exception as exc:  # boundary: preserve failure in the run ledger
        run.status = RunStatus.FAILED
        run.error = str(exc)
        raise WorkflowError(
            f"Agent step '{capability}' failed for lead {lead.id}: {exc}"
        ) from exc
    finally:
        run.completed_at = utc_now()


def prepare_research(lead: Lead, executor: AgentExecutor) -> AgentRun:
    """Move a new lead into research and invoke the research capability."""
    transition(lead, LeadStatus.RESEARCHING)
    return run_step(
        lead,
        "company_researcher",
        executor,
        {"lead": asdict(lead), "objective": "research_company_and_contact"},
    )


def prepare_outreach(lead: Lead, executor: AgentExecutor) -> AgentRun:
    """Prepare an outreach draft; sending is intentionally outside this layer."""
    transition(lead, LeadStatus.READY_FOR_OUTREACH)
    transition(lead, LeadStatus.OUTREACH_PENDING_APPROVAL)
    return run_step(
        lead,
        "outbound_strategy",
        executor,
        {"lead": asdict(lead), "objective": "draft_outreach_for_human_approval"},
    )
