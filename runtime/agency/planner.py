"""Pick the right skill for a user request.

Two-stage:
1. Pre-filter via the SkillRegistry's keyword search (fast, free).
2. Ask the planner LLM to pick the best slug from the shortlist.

If the LLM is unavailable we fall back to the top keyword match.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .llm import AnthropicLLM, LLMError
from .skills import Skill, SkillRegistry


@dataclass
class PlanResult:
    skill: Skill
    rationale: str
    candidates: list[Skill]


PLANNER_SYSTEM = (
    "You route user requests to specialized AI agents. "
    "You will be given a request and a numbered list of candidate agents. "
    "Reply with ONLY a JSON object: "
    '{"choice": <number>, "rationale": "<one short sentence>"} '
    "Pick the single best agent for the request. No prose, no code fences."
)


class Planner:
    def __init__(self, registry: SkillRegistry, llm: AnthropicLLM | None = None,
                 shortlist_size: int = 8):
        self.registry = registry
        self.llm = llm
        self.shortlist_size = shortlist_size

    def plan(self, request: str, hint_slug: str | None = None) -> PlanResult:
        if hint_slug:
            skill = self.registry.by_slug(hint_slug)
            if skill is None:
                raise ValueError(f"Unknown skill slug: {hint_slug}")
            return PlanResult(skill=skill, rationale="explicit user choice", candidates=[skill])

        candidates = self.registry.search(request, limit=self.shortlist_size)
        if not candidates:
            candidates = self.registry.all()[: self.shortlist_size]

        if len(candidates) == 1 or self.llm is None:
            return PlanResult(
                skill=candidates[0],
                rationale="top keyword match" if self.llm is None else "only candidate",
                candidates=candidates,
            )

        try:
            choice_idx, rationale = self._ask_llm(request, candidates)
        except LLMError:
            return PlanResult(
                skill=candidates[0],
                rationale="LLM unavailable, fell back to top keyword match",
                candidates=candidates,
            )
        if choice_idx < 0 or choice_idx >= len(candidates):
            choice_idx = 0
        return PlanResult(skill=candidates[choice_idx], rationale=rationale, candidates=candidates)

    def _ask_llm(self, request: str, candidates: list[Skill]) -> tuple[int, str]:
        assert self.llm is not None
        lines = [f"{i+1}. {c.name} ({c.category}) — {c.description}" for i, c in enumerate(candidates)]
        prompt = f"Request:\n{request}\n\nCandidates:\n" + "\n".join(lines)
        resp = self.llm.messages_create(
            system=PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            model=self.llm.config.planner_model,
            max_tokens=200,
        )
        text = _first_text(resp)
        return _parse_choice(text)


def _first_text(resp) -> str:
    for block in getattr(resp, "content", []):
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_choice(text: str) -> tuple[int, str]:
    """Parse the planner's JSON. Tolerant of stray prose around the JSON."""
    match = _JSON_RE.search(text)
    if not match:
        return 0, "could not parse planner response"
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return 0, "could not decode planner JSON"
    choice = data.get("choice", 1)
    try:
        idx = int(choice) - 1
    except (TypeError, ValueError):
        idx = 0
    rationale = str(data.get("rationale", "no rationale provided")).strip()
    return idx, rationale
