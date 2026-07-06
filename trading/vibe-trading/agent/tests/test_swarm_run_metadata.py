"""Unit tests for run-level provider/model metadata on SwarmRun.

The fields capture which LLM provider/model the swarm was launched against
so ``.swarm/runs/<id>/run.json`` carries enough context for cost audits
and post-hoc debugging. The tests assert the new fields are accepted,
default cleanly, and that legacy run.json files (which predate the
fields) still parse — important because existing on-disk runs will be
re-read by ``SwarmStore.list_runs`` after this change.
"""

from __future__ import annotations

import pytest

from src.swarm.models import SwarmRun


def _base_kwargs() -> dict:
    """Required-only kwargs for a SwarmRun instance."""
    return {
        "id": "swarm-test",
        "preset_name": "dummy_preset",
        "created_at": "2026-05-09T00:00:00+00:00",
    }


def test_provider_and_model_persist_on_construction() -> None:
    """Explicitly-supplied provider/model should appear in serialization."""
    run = SwarmRun(**_base_kwargs(), provider="openai", model="gpt-4o")

    assert run.provider == "openai"
    assert run.model == "gpt-4o"

    # Round-trip through JSON to mirror the .swarm/runs/<id>/run.json path.
    blob = run.model_dump_json()
    rehydrated = SwarmRun.model_validate_json(blob)
    assert rehydrated.provider == "openai"
    assert rehydrated.model == "gpt-4o"


def test_provider_and_model_default_to_none() -> None:
    """Both fields are optional and default to None."""
    run = SwarmRun(**_base_kwargs())

    assert run.provider is None
    assert run.model is None


def test_legacy_run_json_without_provider_model_still_parses() -> None:
    """Existing run.json files predate provider/model and must still load.

    SwarmStore.get_run / list_runs reads on-disk JSON via
    ``SwarmRun.model_validate_json``. Adding required fields would silently
    break those flows; we want absent keys to deserialize to the default.
    """
    legacy_blob = (
        '{"id":"legacy-run","preset_name":"old","status":"completed",'
        '"created_at":"2026-01-01T00:00:00+00:00",'
        '"total_input_tokens":12345,"total_output_tokens":678}'
    )
    run = SwarmRun.model_validate_json(legacy_blob)

    assert run.id == "legacy-run"
    assert run.provider is None
    assert run.model is None
    # Untouched fields still come through.
    assert run.total_input_tokens == 12345
    assert run.total_output_tokens == 678


@pytest.mark.parametrize(
    ("provider", "model"),
    [
        ("anthropic", "claude-sonnet-4-5"),
        ("deepseek", "deepseek-v3"),
        ("openrouter", "openai/gpt-5"),
    ],
)
def test_accepts_other_providers(provider: str, model: str) -> None:
    """Field accepts any string — provider list is not enumerated at runtime."""
    run = SwarmRun(**_base_kwargs(), provider=provider, model=model)
    assert run.provider == provider
    assert run.model == model
