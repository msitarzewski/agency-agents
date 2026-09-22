"""Turn an existing Agency Agent markdown file into an executable capability."""

from pathlib import Path
from typing import Any, Dict

from .agent_loader import AgentCatalog
from providers.openai_compatible import OpenAICompatibleProvider


CAPABILITY_INSTRUCTIONS = {
    "company_researcher": "Research the company and contact using ONLY evidence supplied in the input. Do not invent facts. Return JSON with summary, evidence, signals, and unknowns.",
    "qualification": "Score fit for the user's ecommerce operations-automation service. Use only supplied evidence. Return JSON with score_0_100, fit, reasons, buying_signals, and disqualifiers.",
    "pain_detector": "Identify evidence-backed operational pain points that the service could solve. Separate observed evidence from hypotheses. Return JSON with pain_points, evidence, confidence, and missing_evidence.",
    "outbound_strategy": "Draft concise personalized outreach based on verified evidence. Do not claim anything not in the input. Return JSON with channel, subject, body, personalization_evidence, CTA, and send=false.",
}


class LLMExecutor:
    def __init__(self, repo_root: Path, provider: OpenAICompatibleProvider):
        self.catalog = AgentCatalog(repo_root)
        self.provider = provider

    def __call__(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if capability not in CAPABILITY_INSTRUCTIONS:
            raise ValueError(f"No LLM instructions configured for capability: {capability}")
        persona = self.catalog.load(
            "outbound_strategy" if capability == "outbound_strategy" else capability
        )
        system = (
            "You are executing one specialist from the Agency Agents repository.\n\n"
            "SPECIALIST PERSONA:\n" + persona + "\n\n"
            "EXECUTION RULES:\n" + CAPABILITY_INSTRUCTIONS[capability] + "\n"
            "Return ONLY a valid JSON object."
        )
        import json
        user = "Structured workflow context:\n" + json.dumps(context, ensure_ascii=False, default=str, indent=2)
        return self.provider.generate_json(system, user)
