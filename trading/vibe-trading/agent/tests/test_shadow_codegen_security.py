"""Security tests for Shadow Account code generation."""

from __future__ import annotations

import ast

import pytest

from src.shadow_account.codegen import render_signal_engine, validate_generated
from src.shadow_account.models import ShadowProfile, ShadowRule


def _malicious_profile() -> ShadowProfile:
    """Build a profile whose dynamic strings look like Python code."""
    rule_id = 'R1"""\nINJECTED_RULE_ID = "boom"\n"""'
    market = 'china_a"""\nINJECTED_MARKET = "boom"\n"""'
    return ShadowProfile(
        shadow_id='shadow_abc"""\nINJECTED_SHADOW_ID = "boom"\n"""',
        created_at="2026-05-05T00:00:00Z",
        journal_hash="deadbeef",
        source_market="china_a",
        profitable_roundtrips=7,
        total_roundtrips=11,
        date_range=(
            '2026-01-01"; INJECTED_START = "boom"; #',
            '2026-01-31\nINJECTED_END = "boom"',
        ),
        profile_text="security regression profile",
        rules=(
            ShadowRule(
                rule_id=rule_id,
                human_text="security regression rule",
                entry_condition={
                    "market": market,
                    "entry_hour": {"min": 9, "max": 15},
                },
                exit_condition={},
                holding_days_range=(2, 4),
                support_count=3,
                coverage_rate=0.42,
                sample_trades=("600519.SH@2026-01-05",),
                weight=0.75,
            ),
        ),
        preferred_markets=(
            'china_a"; INJECTED_PREFERRED = "boom"; #',
            'us\nINJECTED_PREFERRED_2 = "boom"',
        ),
        typical_holding_days=(2.0, 4.0),
    )


@pytest.mark.unit
def test_render_signal_engine_escapes_python_literals_for_dynamic_values() -> None:
    """LLM/user strings must stay data, never executable generated code."""
    profile = _malicious_profile()
    source = render_signal_engine(profile)

    tree = ast.parse(source)
    ok, err = validate_generated(source)
    assert ok, f"generated source failed validation: {err}"

    stored_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    assert not any(name.startswith("INJECTED_") for name in stored_names)

    namespace: dict[str, object] = {"__name__": "shadow_codegen_security_test"}
    exec(compile(source, "<generated-signal-engine>", "exec"), namespace)

    assert not any(name.startswith("INJECTED_") for name in namespace)
    assert namespace["SHADOW_ID"] == profile.shadow_id
    assert namespace["PREFERRED_MARKETS"] == list(profile.preferred_markets)

    rules = namespace["RULES"]
    assert isinstance(rules, list)
    assert rules[0]["rule_id"] == profile.rules[0].rule_id
    assert rules[0]["market"] == profile.rules[0].entry_condition["market"]
