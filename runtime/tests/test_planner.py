"""Planner tests with a stubbed LLM."""

from dataclasses import dataclass

from agency.planner import Planner, _parse_choice
from agency.skills import SkillRegistry, discover_repo_root


@dataclass
class _FakeBlock:
    type: str
    text: str


@dataclass
class _FakeResp:
    content: list


@dataclass
class _FakeConfig:
    planner_model: str = "fake-haiku"


class _StubLLM:
    """Implements just enough of AnthropicLLM for the planner tests."""

    def __init__(self, response_text: str):
        self.response_text = response_text
        self.config = _FakeConfig()
        self.calls: list[dict] = []

    def messages_create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResp(content=[_FakeBlock(type="text", text=self.response_text)])


def test_parse_choice_well_formed():
    idx, rationale = _parse_choice('{"choice": 3, "rationale": "best fit"}')
    assert idx == 2
    assert rationale == "best fit"


def test_parse_choice_with_surrounding_prose():
    text = 'Sure, here is my pick: {"choice": 1, "rationale": "obvious"} done.'
    idx, rationale = _parse_choice(text)
    assert idx == 0
    assert rationale == "obvious"


def test_parse_choice_garbage_falls_back_to_zero():
    idx, rationale = _parse_choice("no json here")
    assert idx == 0
    assert "could not parse" in rationale


def test_planner_uses_hint_slug():
    reg = SkillRegistry.load(discover_repo_root())
    target = reg.all()[0]
    planner = Planner(reg, llm=None)
    plan = planner.plan("any request", hint_slug=target.slug)
    assert plan.skill is target


def test_planner_falls_back_to_first_when_llm_missing():
    reg = SkillRegistry.load(discover_repo_root())
    planner = Planner(reg, llm=None)
    plan = planner.plan("frontend developer needed")
    assert plan.skill is not None
    assert plan.candidates


def test_planner_calls_stub_llm_and_picks_correctly():
    reg = SkillRegistry.load(discover_repo_root())
    stub = _StubLLM('{"choice": 2, "rationale": "test pick"}')
    planner = Planner(reg, llm=stub)
    plan = planner.plan("write a marketing campaign")
    # The stub picks index 1 from whatever shortlist surfaces.
    assert plan.skill is plan.candidates[1]
    assert "test pick" in plan.rationale
    assert stub.calls, "stub LLM was never called"
