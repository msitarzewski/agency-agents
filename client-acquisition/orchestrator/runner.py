"""Executable phase-2 runner for the client-acquisition workflow.

The runner is provider-agnostic: an AgentExecutor can be backed by an LLM,
Claude Code, Codex, a local model, or a deterministic test adapter. External
side effects remain behind explicit adapters and approval gates.
"""

from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .models import AgentRun, Lead, LeadStatus
from .state_machine import transition
from .workflow import WorkflowError, run_step

AgentExecutor = Callable[[str, Dict[str, Any]], Dict[str, Any]]


class ApprovalRequired(RuntimeError):
    """Raised when the workflow reaches a human approval boundary."""


class AgentRunner:
    """Runs agent steps with bounded retries and an in-memory run ledger."""

    def __init__(self, executor: AgentExecutor, max_retries: int = 2):
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        self.executor = executor
        self.max_retries = max_retries
        self.runs: List[AgentRun] = []

    def execute(self, lead: Lead, capability: str, context: Dict[str, Any]) -> AgentRun:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            enriched = dict(context)
            enriched["trace_id"] = enriched.get("trace_id", str(uuid4()))
            enriched["attempt"] = attempt + 1
            try:
                run = run_step(lead, capability, self.executor, enriched)
                self.runs.append(run)
                return run
            except WorkflowError as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise
        raise last_error or WorkflowError("Agent execution failed")

    def run_lead(self, lead: Lead) -> Dict[str, Any]:
        """Run research -> qualification -> pain detection -> outreach draft."""
        trace_id = str(uuid4())
        context: Dict[str, Any] = {"lead": asdict(lead), "trace_id": trace_id}

        if lead.status == LeadStatus.NEW:
            transition(lead, LeadStatus.RESEARCHING)

        research = self.execute(
            lead,
            "company_researcher",
            {**context, "objective": "research_company_and_contact"},
        )
        context["research"] = research.output

        qualification = self.execute(
            lead,
            "qualification",
            {**context, "objective": "score_fit_and_identify_buying_signal"},
        )
        context["qualification"] = qualification.output

        if lead.status == LeadStatus.RESEARCHING:
            transition(lead, LeadStatus.QUALIFIED)
            transition(lead, LeadStatus.READY_FOR_OUTREACH)

        pain = self.execute(
            lead,
            "pain_detector",
            {**context, "objective": "identify_evidence_based_business_pain"},
        )
        context["pain_points"] = pain.output

        transition(lead, LeadStatus.OUTREACH_PENDING_APPROVAL)
        outreach = self.execute(
            lead,
            "outbound_strategy",
            {**context, "objective": "draft_personalized_outreach_no_send"},
        )
        context["outreach"] = outreach.output

        return {
            "trace_id": trace_id,
            "lead": asdict(lead),
            "status": lead.status.value,
            "runs": [asdict(run) for run in self.runs if run.lead_id == lead.id],
            "approval_required": True,
        }


def deterministic_demo_executor(agent: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Safe local executor used by the CLI demo; it never calls an external service."""
    lead = context.get("lead", {})
    company = lead.get("company_name") or "Unknown company"
    name = lead.get("contact_name") or "there"

    if agent == "company_researcher":
        return {"company": company, "summary": "Demo research only; connect a provider for live research."}
    if agent == "qualification":
        return {"score": 75, "fit": True, "reason": "Demo qualification; replace with model-backed scoring."}
    if agent == "pain_detector":
        return {"pain_points": [], "confidence": 0.0, "note": "No live evidence in demo mode."}
    if agent == "outbound_strategy":
        return {
            "subject": f"Idea for {company}",
            "body": f"Hi {name},\n\nI noticed an opportunity to improve an operational workflow at {company}.\n\nWould a short conversation be useful?",
            "send": False,
        }
    raise ValueError(f"Unknown capability: {agent}")
