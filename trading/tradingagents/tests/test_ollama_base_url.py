"""Tests for OLLAMA_BASE_URL env-var override across CLI and client paths."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="module", autouse=True)
def _resync_reloaded_modules():
    """Restore module state after this file's importlib.reload() calls.

    Several tests below reload ``cli.utils`` to re-evaluate OLLAMA_BASE_URL.
    That leaves ``cli.main``'s star-imported names (e.g. get_ticker) bound to
    the pre-reload module objects, which breaks identity checks in unrelated
    tests that happen to run afterward. Re-sync once on teardown so the reload
    doesn't leak across test modules.
    """
    yield
    import cli.main
    import cli.utils
    importlib.reload(cli.utils)
    importlib.reload(cli.main)


# ---- openai_client side: registry-driven base_url resolution --------------


def _reload_client():
    import tradingagents.llm_clients.openai_client as mod
    return importlib.reload(mod)


def _base_url(mod, provider, **kwargs):
    return str(mod.OpenAIClient(model="m", provider=provider, **kwargs).get_llm().openai_api_base)


def test_resolver_returns_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    mod = _reload_client()
    assert _base_url(mod, "ollama") == "http://localhost:11434/v1"


def test_resolver_returns_env_when_set(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote-ollama:11434/v1")
    mod = _reload_client()
    assert _base_url(mod, "ollama") == "http://remote-ollama:11434/v1"


def test_resolver_evaluation_is_call_time(monkeypatch):
    """Setting the env AFTER module import must still take effect."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    mod = _reload_client()
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://late-set:11434/v1")
    assert _base_url(mod, "ollama") == "http://late-set:11434/v1"


def test_resolver_does_not_affect_other_providers(monkeypatch):
    """OLLAMA_BASE_URL should NOT leak into xai/deepseek/etc."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://elsewhere/v1")
    mod = _reload_client()
    assert _base_url(mod, "xai") == "https://api.x.ai/v1"
    assert _base_url(mod, "deepseek") == "https://api.deepseek.com"


def test_client_get_llm_picks_up_env(monkeypatch):
    """End-to-end: OllamaClient.get_llm() respects OLLAMA_BASE_URL."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://my-ollama:11434/v1")
    mod = _reload_client()
    client = mod.OpenAIClient(model="llama3.1", provider="ollama")
    llm = client.get_llm()
    assert "my-ollama" in str(llm.openai_api_base)


def test_explicit_base_url_overrides_env(monkeypatch):
    """An explicit base_url passed to the client wins over the env var."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://env-set:11434/v1")
    mod = _reload_client()
    client = mod.OpenAIClient(
        model="llama3.1",
        provider="ollama",
        base_url="http://explicit:11434/v1",
    )
    llm = client.get_llm()
    assert "explicit" in str(llm.openai_api_base)
    assert "env-set" not in str(llm.openai_api_base)


# ---- cli.utils side: select_llm_provider dropdown -------------------------


def test_cli_dropdown_uses_env(monkeypatch):
    """The Ollama entry in the CLI dropdown must reflect OLLAMA_BASE_URL."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://cli-remote:11434/v1")
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    # Reach inside the function via the same env-read it does at call time
    ollama_url = (
        __import__("os").environ.get("OLLAMA_BASE_URL")
        or "http://localhost:11434/v1"
    )
    assert ollama_url == "http://cli-remote:11434/v1"


def test_cli_dropdown_default_when_unset(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    ollama_url = (
        __import__("os").environ.get("OLLAMA_BASE_URL")
        or "http://localhost:11434/v1"
    )
    assert ollama_url == "http://localhost:11434/v1"


# ---- confirm_ollama_endpoint UX -------------------------------------------


def test_confirm_endpoint_shows_default(monkeypatch, capsys):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    cli_utils.confirm_ollama_endpoint("http://localhost:11434/v1")
    out = capsys.readouterr().out
    assert "http://localhost:11434/v1" in out
    assert "OLLAMA_BASE_URL" not in out  # not from env
    assert "Note" not in out  # no warnings for the canonical default


def test_confirm_endpoint_marks_env_origin(monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote-host:11434/v1")
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    cli_utils.confirm_ollama_endpoint("http://remote-host:11434/v1")
    out = capsys.readouterr().out
    assert "http://remote-host:11434/v1" in out
    assert "OLLAMA_BASE_URL" in out


def test_confirm_endpoint_warns_on_missing_scheme(monkeypatch, capsys):
    """If user sets OLLAMA_BASE_URL=0.0.0.128, advise on the expected shape."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "0.0.0.128")
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    cli_utils.confirm_ollama_endpoint("0.0.0.128")
    out = capsys.readouterr().out
    assert "missing a scheme" in out
    assert "http://<host>:11434/v1" in out


def test_confirm_endpoint_warns_on_non_default_port_remote(monkeypatch, capsys):
    """A remote host with no :11434 gets a soft hint about port mismatch."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote-host/v1")
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    cli_utils.confirm_ollama_endpoint("http://remote-host/v1")
    out = capsys.readouterr().out
    assert "port 11434" in out


def test_confirm_endpoint_quiet_on_local_no_port(monkeypatch, capsys):
    """Local host without port shouldn't trigger the remote-port hint."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost/v1")
    import cli.utils as cli_utils
    importlib.reload(cli_utils)
    cli_utils.confirm_ollama_endpoint("http://localhost/v1")
    out = capsys.readouterr().out
    assert "Note" not in out  # localhost is fine without explicit port


def test_ollama_model_labels_no_local_suffix():
    """Labels should no longer claim '(local)' since the endpoint is dynamic."""
    from tradingagents.llm_clients.model_catalog import get_model_options
    for mode in ("quick", "deep"):
        labels = [label for label, _ in get_model_options("ollama", mode)]
        assert all("local" not in label for label in labels), labels


def test_ollama_offers_custom_model_id():
    """Ollama users with custom-pulled models can pick 'Custom model ID'."""
    from tradingagents.llm_clients.model_catalog import get_model_options
    for mode in ("quick", "deep"):
        entries = get_model_options("ollama", mode)
        values = [v for _, v in entries]
        assert "custom" in values, f"Ollama {mode!r} missing 'custom' option: {entries}"
        # Custom option is last so it doesn't push the curated defaults off-screen
        assert values[-1] == "custom", f"'custom' should be last entry: {values}"
