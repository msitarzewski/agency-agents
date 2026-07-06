"""G1 evidence: anchored redaction — no over-redaction, idempotent, None-safe."""

from __future__ import annotations

from pathlib import Path

from src.tools.redaction import _internal_roots, redact_internal_paths


def test_none_and_empty_and_nonstr_safe():
    assert redact_internal_paths(None) == ""
    assert redact_internal_paths("") == ""
    assert redact_internal_paths(42) == "42"


def test_internal_leak_is_redacted_but_tail_kept():
    leak = str(Path.cwd() / "agent" / "runs" / "RUN42" / "run.json")
    out = redact_internal_paths(leak)
    assert "<redacted>" in out
    assert str(Path.cwd()) not in out
    assert "RUN42" in out and "run.json" in out


def test_no_over_redaction_of_external_or_caller_paths():
    roots = _internal_roots()
    for keep in ("/etc/passwd", "/api/v1/orders", "../../etc/shadow", "D:\\external\\report.csv"):
        assert not any(rt in keep for rt in roots)
        assert redact_internal_paths(f"err: {keep}") == f"err: {keep}"


def test_idempotent():
    leak = str(Path.home() / "agent" / "x" / "run.json")
    once = redact_internal_paths(leak)
    assert redact_internal_paths(once) == once
    assert "<redacted>" in once
