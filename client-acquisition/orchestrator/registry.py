"""Registry that maps workflow capabilities to existing Agency Agents."""

from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]

AGENT_REGISTRY: Dict[str, str] = {
    "lead_generation": "sales/sales-offer-lead-gen-strategist.md",
    "outbound_strategy": "sales/sales-outbound-strategist.md",
    "qualification": "sales/sales-discovery-coach.md",
    "deal_strategy": "sales/sales-deal-strategist.md",
    "technical_scoping": "sales/sales-engineer.md",
    "pipeline_analysis": "sales/sales-pipeline-analyst.md",
    "proposal": "sales/sales-proposal-strategist.md",
    "orchestration": "engineering/engineering-multi-agent-systems-architect.md",
    "delivery_architecture": "engineering/engineering-software-architect.md",
    "backend_delivery": "engineering/engineering-backend-architect.md",
}


def get_agent_path(capability: str) -> Path:
    try:
        relative_path = AGENT_REGISTRY[capability]
    except KeyError as exc:
        raise KeyError(f"Unknown acquisition capability: {capability}") from exc

    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Registered agent does not exist: {relative_path}")
    return path


def list_capabilities() -> Dict[str, str]:
    return dict(AGENT_REGISTRY)
