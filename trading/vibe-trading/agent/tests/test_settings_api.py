"""Regression tests for local settings API endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_server


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    env_example = tmp_path / ".env.example"
    env_path = tmp_path / ".env"
    env_example.write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=openrouter",
                "LANGCHAIN_MODEL_NAME=deepseek/deepseek-v4-pro",
                "OPENROUTER_BASE_URL=https://openrouter.ai/api/v1",
                "OPENROUTER_API_KEY=sk-or-v1-your-key-here",
                "LANGCHAIN_TEMPERATURE=0.2",
                "TIMEOUT_SECONDS=90",
                "MAX_RETRIES=3",
                "LANGCHAIN_REASONING_EFFORT=max",
                "TUSHARE_TOKEN=your-tushare-token",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)
    monkeypatch.setattr(api_server, "ENV_EXAMPLE_PATH", env_example)
    monkeypatch.setattr(api_server, "_baostock_supported", lambda: False)
    monkeypatch.setattr(api_server, "_baostock_installed", lambda: False)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    return TestClient(api_server.app, client=("127.0.0.1", 50000))


def test_get_llm_settings_is_side_effect_free_and_hides_placeholders(
    client: TestClient, tmp_path: Path,
) -> None:
    response = client.get("/settings/llm")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openrouter"
    assert body["model_name"] == "deepseek/deepseek-v4-pro"
    assert body["api_key_configured"] is False
    assert body["api_key_hint"] is None
    assert not Path(body["env_path"]).is_absolute()
    assert body["env_path"].endswith(".env")
    assert body["reasoning_effort"] == "max"
    assert not (tmp_path / ".env").exists()


@pytest.mark.parametrize("placeholder", ["sk-xxx", "xxx", "gsk_xxx"])
def test_llm_settings_treat_documented_key_placeholders_as_unconfigured(
    client: TestClient, tmp_path: Path, placeholder: str,
) -> None:
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=deepseek",
                "LANGCHAIN_MODEL_NAME=deepseek-v4-pro",
                f"DEEPSEEK_API_KEY={placeholder}",
                "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    response = client.get("/settings/llm")

    assert response.status_code == 200
    body = response.json()
    assert body["api_key_configured"] is False
    assert body["api_key_hint"] is None
    assert placeholder not in response.text


def test_update_llm_settings_persists_project_env(
    client: TestClient, tmp_path: Path,
) -> None:
    response = client.put(
        "/settings/llm",
        json={
            "provider": "openrouter",
            "model_name": "deepseek/deepseek-v4-pro",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "or-secret-value",
            "temperature": 0.1,
            "timeout_seconds": 45,
            "max_retries": 1,
            "reasoning_effort": "max",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openrouter"
    assert body["api_key_configured"] is True
    assert body["api_key_hint"] is None
    assert "or-secret-value" not in response.text
    assert "or-s...alue" not in response.text

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "LANGCHAIN_PROVIDER=openrouter" in env_text
    assert "OPENROUTER_API_KEY=or-secret-value" in env_text
    assert "LANGCHAIN_REASONING_EFFORT=max" in env_text
    assert "sk-or-v1-your-key-here" not in env_text


def test_get_data_source_settings_treats_placeholder_as_unconfigured(
    client: TestClient, tmp_path: Path,
) -> None:
    response = client.get("/settings/data-sources")

    assert response.status_code == 200
    body = response.json()
    assert body["tushare_token_configured"] is False
    assert body["tushare_token_hint"] is None
    assert body["baostock_supported"] is False
    assert body["baostock_installed"] is False
    assert not Path(body["env_path"]).is_absolute()
    assert body["env_path"].endswith(".env")
    assert not (tmp_path / ".env").exists()


def test_settings_response_never_exposes_configured_secret_hints(
    client: TestClient, tmp_path: Path,
) -> None:
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=openrouter",
                "OPENROUTER_API_KEY=or-secret-private-value",
                "TUSHARE_TOKEN=ts-secret-private-token",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    llm_response = client.get("/settings/llm")
    data_response = client.get("/settings/data-sources")

    assert llm_response.status_code == 200
    assert data_response.status_code == 200
    llm_body = llm_response.json()
    data_body = data_response.json()
    assert llm_body["api_key_configured"] is True
    assert llm_body["api_key_hint"] is None
    assert data_body["tushare_token_configured"] is True
    assert data_body["tushare_token_hint"] is None
    assert "or-secret-private-value" not in llm_response.text
    assert "or-s...alue" not in llm_response.text
    assert "ts-secret-private-token" not in data_response.text
    assert "ts-s...oken" not in data_response.text


def test_settings_reads_reject_remote_dev_mode_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_example = tmp_path / ".env.example"
    env_path.write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=openrouter",
                "OPENROUTER_API_KEY=or-secret-value",
                "TUSHARE_TOKEN=ts-secret-token",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env_example.write_text("LANGCHAIN_PROVIDER=openai\n", encoding="utf-8")
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)
    monkeypatch.setattr(api_server, "ENV_EXAMPLE_PATH", env_example)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    remote_client = TestClient(api_server.app, client=("203.0.113.10", 50000))

    llm_response = remote_client.get("/settings/llm")
    data_source_response = remote_client.get("/settings/data-sources")

    assert llm_response.status_code == 403
    assert data_source_response.status_code == 403
    assert "or-s...alue" not in llm_response.text
    assert "ts-s...oken" not in data_source_response.text


def test_settings_reads_allow_loopback_without_bearer_even_when_api_auth_key_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_example = tmp_path / ".env.example"
    env_path.write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=openrouter",
                "OPENROUTER_API_KEY=or-secret-value",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env_example.write_text("LANGCHAIN_PROVIDER=openai\n", encoding="utf-8")
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)
    monkeypatch.setattr(api_server, "ENV_EXAMPLE_PATH", env_example)
    monkeypatch.setenv("API_AUTH_KEY", "settings-secret")
    local_client = TestClient(api_server.app, client=("127.0.0.1", 50000))

    unauthenticated_response = local_client.get("/settings/llm")
    authenticated_response = local_client.get(
        "/settings/llm",
        headers={"Authorization": "Bearer settings-secret"},
    )

    assert unauthenticated_response.status_code == 200
    assert authenticated_response.status_code == 200
    assert authenticated_response.json()["api_key_configured"] is True
    assert authenticated_response.json()["api_key_hint"] is None
    assert "or-secret-value" not in authenticated_response.text
    assert "or-s...alue" not in authenticated_response.text


def test_update_data_source_settings_persists_tushare_token(
    client: TestClient, tmp_path: Path,
) -> None:
    response = client.put(
        "/settings/data-sources",
        json={"tushare_token": "ts-secret-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tushare_token_configured"] is True
    assert body["tushare_token_hint"] is None
    assert "ts-secret-token" not in response.text
    assert "ts-s...oken" not in response.text

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "TUSHARE_TOKEN=ts-secret-token" in env_text


def test_settings_writes_reject_remote_dev_mode_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_example = tmp_path / ".env.example"
    env_path = tmp_path / ".env"
    env_example.write_text("LANGCHAIN_PROVIDER=openai\n", encoding="utf-8")
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)
    monkeypatch.setattr(api_server, "ENV_EXAMPLE_PATH", env_example)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    remote_client = TestClient(api_server.app, client=("203.0.113.10", 50000))

    response = remote_client.put(
        "/settings/data-sources",
        json={"tushare_token": "ts-secret-token"},
    )

    assert response.status_code == 403
    assert not env_path.exists()
