"""Security regression tests for upload file type restrictions."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_server


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(api_server, "UPLOADS_DIR", tmp_path)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    monkeypatch.setattr(api_server, "_API_KEY", "")
    return TestClient(api_server.app, client=("127.0.0.1", 50000))


@pytest.mark.parametrize(
    "filename",
    [
        "payload.py",
        "run.sh",
        "config.yaml",
        "config.yml",
        "template.j2",
        "Dockerfile",
    ],
)
def test_upload_blocks_executable_adjacent_files(
    client: TestClient,
    tmp_path: Path,
    filename: str,
) -> None:
    response = client.post(
        "/upload",
        files={"file": (filename, b"content", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []
