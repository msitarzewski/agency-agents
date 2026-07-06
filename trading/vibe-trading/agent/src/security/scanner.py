"""Prompt-injection warning scanner for external tool content.

The scanner is intentionally conservative in action: it never rewrites or
drops fetched content. It only adds warning metadata to the JSON envelopes
returned by reader/search tools so downstream agents can treat external text
as untrusted instructions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class InjectionRule:
    """A prompt-injection pattern and its warning metadata."""

    rule_id: str
    pattern: re.Pattern[str]
    severity: str
    message: str


_RULES: tuple[InjectionRule, ...] = (
    InjectionRule(
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget|bypass|override)\b.{0,80}"
            r"\b(previous|prior|above|earlier|system|developer)\b.{0,40}"
            r"\b(instructions?|rules?|messages?|prompt)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "high",
        "External content appears to request overriding prior instructions.",
    ),
    InjectionRule(
        "system_prompt_exfiltration",
        re.compile(
            r"\b(reveal|print|show|dump|leak|exfiltrate)\b.{0,80}"
            r"\b(system|developer|hidden)\b.{0,40}\b(prompt|instructions?|rules?|message)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "high",
        "External content appears to request hidden prompt or instruction disclosure.",
    ),
    InjectionRule(
        "role_or_channel_claim",
        re.compile(
            r"\b(system|developer)\s+message\b|\byou are now\b.{0,50}"
            r"\b(system|developer|admin|root)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "medium",
        "External content appears to impersonate a privileged role or channel.",
    ),
    InjectionRule(
        "secret_exfiltration",
        re.compile(
            r"\b(print|show|dump|send|exfiltrate|leak)\b.{0,80}"
            r"\b(api[_ -]?keys?|tokens?|passwords?|secrets?|env(?:ironment)? vars?)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "high",
        "External content appears to request secret or environment disclosure.",
    ),
    InjectionRule(
        "tool_abuse",
        re.compile(
            r"\b(call|run|execute|use)\b.{0,80}\b(shell|bash|terminal|python|curl)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "medium",
        "External content appears to instruct tool or shell execution.",
    ),
)


def scan_prompt_injection(text: str, *, field: str | None = None) -> list[dict[str, str]]:
    """Return prompt-injection findings for untrusted external text.

    Args:
        text: External text to scan.
        field: Optional JSON field path used in warning output.

    Returns:
        A stable list of warning dictionaries. At most one finding is emitted
        per rule.
    """
    findings: list[dict[str, str]] = []
    if not text:
        return findings

    for rule in _RULES:
        match = rule.pattern.search(text)
        if not match:
            continue
        finding = {
            "type": "prompt_injection",
            "rule_id": rule.rule_id,
            "severity": rule.severity,
            "message": rule.message,
            "match": _compact_match(match.group(0)),
        }
        if field is not None:
            finding["field"] = field
        findings.append(finding)
    return findings


def with_security_warnings(
    payload: dict[str, Any],
    *,
    fields: Iterable[str],
) -> dict[str, Any]:
    """Attach security warnings for selected string fields in a payload.

    Field selectors are dotted paths. The ``*`` component iterates lists, e.g.
    ``results.*.snippet`` scans every result snippet and reports fields as
    ``results.0.snippet``.

    Args:
        payload: JSON-serializable tool response payload.
        fields: Dotted field selectors to scan.

    Returns:
        The same payload object with a ``security_warnings`` list added when
        any finding is detected.
    """
    warnings: list[dict[str, str]] = []
    for selector in fields:
        for path, value in _iter_selected_values(payload, selector.split(".")):
            if isinstance(value, str):
                warnings.extend(scan_prompt_injection(value, field=path))

    if warnings:
        existing = payload.get("security_warnings", [])
        if isinstance(existing, list):
            payload["security_warnings"] = [*existing, *warnings]
        else:
            payload["security_warnings"] = warnings
    return payload


def _iter_selected_values(
    value: Any,
    parts: list[str],
    path: str = "",
) -> Iterable[tuple[str, Any]]:
    """Yield ``(field_path, value)`` pairs selected by a dotted path."""
    if not parts:
        yield path, value
        return

    head, *tail = parts
    if head == "*":
        if not isinstance(value, list):
            return
        for idx, item in enumerate(value):
            next_path = f"{path}.{idx}" if path else str(idx)
            yield from _iter_selected_values(item, tail, next_path)
        return

    if not isinstance(value, dict) or head not in value:
        return
    next_path = f"{path}.{head}" if path else head
    yield from _iter_selected_values(value[head], tail, next_path)


def _compact_match(text: str) -> str:
    """Return a short, single-line match excerpt for warning metadata."""
    compact = " ".join(text.split())
    if len(compact) <= 120:
        return compact
    return compact[:117] + "..."
