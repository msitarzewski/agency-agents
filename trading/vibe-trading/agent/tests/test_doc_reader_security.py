"""Security regression tests for document and broker-file path boundaries."""

from __future__ import annotations

import json

import pytest

from src.tools.doc_reader_tool import read_document
from src.tools.path_utils import safe_document_path, safe_user_path


@pytest.fixture(autouse=True)
def clear_allowed_roots(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start each test with only the built-in import roots."""
    monkeypatch.delenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", raising=False)


def _read_json(result: str) -> dict:
    """Parse a document-reader JSON envelope."""
    return json.loads(result)


def test_read_document_rejects_system_paths() -> None:
    result = _read_json(read_document("/etc/passwd"))

    assert result["status"] == "error"
    assert "outside allowed document roots" in result["error"]


def test_safe_user_path_rejects_root_home_credentials() -> None:
    with pytest.raises(ValueError, match="outside allowed user-file roots"):
        safe_user_path("/root/.aws/credentials")


def test_read_document_allows_configured_import_root(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc = tmp_path / "note.txt"
    doc.write_text("VT_DOC_OK", encoding="utf-8")
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))

    result = _read_json(read_document(str(doc)))

    assert result["status"] == "ok"
    assert result["text"] == "VT_DOC_OK"
    assert safe_document_path(str(doc)) == doc.resolve()
