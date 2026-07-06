"""Shared redaction helpers promoted from the swarm worker (#142 → public).

Covers ``redact_payload`` (recursive sensitive-key scrubbing) and
``is_sensitive_arg`` (key-name classification), now consumed by the swarm
worker and the live-action audit ledger from one module.
"""

from __future__ import annotations

import pytest

from src.tools.redaction import is_sensitive_arg, redact_payload


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "Authorization",
        "  TOKEN  ",
        "password",
        "passphrase",
        "secret",
        "headers",
        "content",
        "env",
        "api_token",  # marker substring
        "access_token",  # marker substring
        "x-authorization",  # marker substring
        "client_secret",  # marker substring
    ],
)
def test_is_sensitive_arg_matches(key: str) -> None:
    assert is_sensitive_arg(key) is True


@pytest.mark.parametrize(
    "key",
    [
        "account_number",
        "account_id",
        "account_no",
        "account_num",
        "brokerage_account_number",
        "account_url",
        "rhs_account_number",
        "ssn",
        "social_security_number",
        "tax_id",
        "taxpayer_id",
        "tin",
        "routing_number",
        "bank_account_number",
        "  Account_Number  ",  # normalized (stripped, lower-cased)
    ],
)
def test_is_sensitive_arg_matches_account_pii(key: str) -> None:
    """H1: curated exact account/PII field names redact."""
    assert is_sensitive_arg(key) is True


@pytest.mark.parametrize("key", ["symbol", "side", "quantity", "url", "path", "query"])
def test_is_sensitive_arg_allows_benign_keys(key: str) -> None:
    assert is_sensitive_arg(key) is False


@pytest.mark.parametrize(
    "key",
    [
        "account_ref",  # opaque provenance — SPEC §5 accountability chain
        "account",  # broad token must NOT trip exact-match PII set
        "account_balance",
        "account_type",
        "account_status",
        "accounts",
    ],
)
def test_is_sensitive_arg_preserves_account_ref_and_benign_account_fields(
    key: str,
) -> None:
    """Exact-match (not substring) PII keys keep ``account_ref`` and other
    benign ``account*`` fields readable, preventing over-redaction."""
    assert is_sensitive_arg(key) is False


def test_redact_payload_keeps_account_ref_provenance() -> None:
    """``account_ref`` provenance survives while sibling account numbers/SSN are
    scrubbed (SPEC §5 mandate→consent chain)."""
    out = redact_payload(
        {
            "account_ref": "rh_ref_opaque",
            "account_number": "5XX111",
            "ssn": "123-45-6789",
            "symbol": "NVDA",
        }
    )
    assert out == {
        "account_ref": "rh_ref_opaque",
        "account_number": "[redacted]",
        "ssn": "[redacted]",
        "symbol": "NVDA",
    }


def test_redact_payload_scrubs_top_level_sensitive_keys() -> None:
    out = redact_payload(
        {"symbol": "NVDA", "authorization": "Bearer rh-oauth-token", "qty": 3}
    )
    assert out == {"symbol": "NVDA", "authorization": "[redacted]", "qty": 3}


def test_redact_payload_recurses_into_nested_structures() -> None:
    payload = {
        "broker_request": {"symbol": "AAPL", "headers": {"Authorization": "secret"}},
        "orders": [
            {"id": 1, "access_token": "leak"},
            {"id": 2, "note": "ok"},
        ],
    }
    out = redact_payload(payload)
    assert out == {
        "broker_request": {"symbol": "AAPL", "headers": "[redacted]"},
        "orders": [
            {"id": 1, "access_token": "[redacted]"},
            {"id": 2, "note": "ok"},
        ],
    }


def test_redact_payload_does_not_mutate_input() -> None:
    payload = {"token": "abc", "nested": [{"secret": "x"}]}
    out = redact_payload(payload)
    assert payload == {"token": "abc", "nested": [{"secret": "x"}]}
    assert out["token"] == "[redacted]"
    assert out["nested"][0]["secret"] == "[redacted]"


def test_redact_payload_passes_through_scalars() -> None:
    assert redact_payload("plain string") == "plain string"
    assert redact_payload(42) == 42
    assert redact_payload(None) is None
