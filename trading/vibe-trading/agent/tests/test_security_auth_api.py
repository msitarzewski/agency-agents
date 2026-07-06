"""Security regression tests for API authentication boundaries."""

from __future__ import annotations

import ipaddress
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import api_server


def _remote_client() -> TestClient:
    """Return a TestClient that simulates a non-loopback caller."""
    return TestClient(api_server.app, client=("203.0.113.10", 50000))


def _local_client() -> TestClient:
    """Return a TestClient that simulates a loopback caller."""
    return TestClient(api_server.app, client=("127.0.0.1", 50000))


@pytest.fixture(autouse=True)
def clear_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every auth test from dev-mode auth."""
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    monkeypatch.delenv("VIBE_TRADING_TRUST_DOCKER_LOOPBACK", raising=False)
    monkeypatch.delenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", raising=False)
    monkeypatch.setattr(api_server, "_API_KEY", "")


def test_remote_write_requires_api_key_when_key_unset() -> None:
    response = _remote_client().post("/sessions", json={})

    assert response.status_code == 403
    assert "API_AUTH_KEY" in response.json()["detail"]


def test_remote_goal_endpoints_require_api_key_when_key_unset() -> None:
    client = _remote_client()

    cases = [
        ("post", "/sessions/abcdef012345/goal", {"objective": "Evaluate NVDA", "criteria": ["Define thesis"]}),
        ("get", "/sessions/abcdef012345/goal", None),
        (
            "post",
            "/sessions/abcdef012345/goal/evidence",
            {
                "goal_id": "goal_123",
                "expected_goal_id": "goal_123",
                "text": "Evidence",
            },
        ),
    ]
    for method, path, body in cases:
        kwargs = {"json": body} if body is not None else {}
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 403, f"{method.upper()} {path}"


def test_local_dev_write_allowed_when_key_unset() -> None:
    response = _local_client().post("/sessions", json={})

    assert response.status_code in {201, 501}


def test_docker_gateway_dev_write_allowed_only_with_compose_trust_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="172.18.0.1"))
    monkeypatch.setattr(
        api_server,
        "_default_gateway_ips",
        lambda: {ipaddress.IPv4Address("172.18.0.1")},
    )

    assert not api_server._is_local_client(request)

    monkeypatch.setenv("VIBE_TRADING_TRUST_DOCKER_LOOPBACK", "1")

    assert api_server._is_local_client(request)


def test_docker_network_peer_is_not_local_even_with_compose_trust_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="172.18.0.42"))
    monkeypatch.setenv("VIBE_TRADING_TRUST_DOCKER_LOOPBACK", "1")
    monkeypatch.setattr(
        api_server,
        "_default_gateway_ips",
        lambda: {ipaddress.IPv4Address("172.18.0.1")},
    )

    assert not api_server._is_local_client(request)


def test_configured_api_key_required_for_sensitive_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    client = _remote_client()

    for path in [
        "/runs",
        "/sessions",
        "/sessions/abcdef012345/goal",
        "/swarm/runs",
    ]:
        response = client.get(path)
        assert response.status_code == 401, path


def test_configured_api_key_accepts_bearer_for_sensitive_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _remote_client().get(
        "/runs",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200


def test_loopback_bypasses_auth_even_when_api_key_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loopback clients remain trusted for non-settings reads."""
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    local = _local_client()
    remote = _remote_client()

    # Loopback: no bearer needed → should succeed
    local_response = local.get("/runs")
    assert local_response.status_code == 200

    # Remote without bearer: still rejected
    remote_response = remote.get("/runs")
    assert remote_response.status_code == 401

    # Remote with bearer: accepted
    remote_bearer = remote.get("/runs", headers={"Authorization": "Bearer secret"})
    assert remote_bearer.status_code == 200


def _llm_settings_payload(base_url: str = "https://api.openai.com/v1") -> dict[str, object]:
    return {
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "base_url": base_url,
        "temperature": 0,
        "timeout_seconds": 120,
        "max_retries": 2,
    }


def test_dns_rebound_loopback_cannot_write_llm_settings_without_bearer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Configured API keys must gate credential-routing settings writes."""
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "LANGCHAIN_PROVIDER=openai",
                "LANGCHAIN_MODEL_NAME=gpt-4o-mini",
                "OPENAI_BASE_URL=https://api.openai.com/v1",
                "OPENAI_API_KEY=sk-existing-test-key",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)

    response = _local_client().put(
        "/settings/llm",
        headers={"host": "attacker.example:8899", "origin": "http://attacker.example:8899"},
        json=_llm_settings_payload("https://attacker.example/openai-compatible/v1"),
    )

    # The rebound-host middleware (#242) rejects this loopback request with an
    # attacker-controlled Host before the settings-write auth layer is reached;
    # either layer must prevent the credential-routing write from persisting.
    assert response.status_code == 403
    saved = env_path.read_text(encoding="utf-8")
    assert "https://attacker.example/openai-compatible/v1" not in saved
    assert "OPENAI_BASE_URL=https://api.openai.com/v1" in saved
    assert "OPENAI_API_KEY=sk-existing-test-key" in saved


def test_authorized_client_can_write_llm_settings_when_api_key_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)

    response = _remote_client().put(
        "/settings/llm",
        headers={"Authorization": "Bearer secret"},
        json=_llm_settings_payload("https://api.openai.com/v1"),
    )

    assert response.status_code == 200
    assert "OPENAI_BASE_URL=https://api.openai.com/v1" in env_path.read_text(encoding="utf-8")


def test_local_dev_can_write_llm_settings_when_api_key_unset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_path = tmp_path / ".env"
    monkeypatch.setattr(api_server, "ENV_PATH", env_path)

    response = _local_client().put(
        "/settings/llm",
        json=_llm_settings_payload("https://api.openai.com/v1"),
    )

    assert response.status_code == 200
    assert "OPENAI_BASE_URL=https://api.openai.com/v1" in env_path.read_text(encoding="utf-8")


def test_loopback_rejects_rebound_host_before_auth_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A loopback peer is not enough when Host is attacker-controlled."""
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _local_client().get(
        "/runs",
        headers={"Host": "attacker.example:8899", "Origin": "http://attacker.example:8899"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted local API host"


def test_remote_untrusted_host_still_uses_bearer_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Host gate only narrows loopback trust; remote clients still use API_AUTH_KEY."""
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _remote_client().get(
        "/runs",
        headers={"Host": "attacker.example:8899", "Origin": "http://attacker.example:8899"},
    )

    assert response.status_code == 401


def test_rebound_host_cannot_start_live_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DNS-rebound loopback JSON requests must not reach live-runner control."""
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    monkeypatch.setattr(api_server, "_active_mandate_state", lambda broker: SimpleNamespace(expired=False))

    reached = {"factory": False}

    class DummyRunner:
        async def run_loop(self):
            return None

    def build_runner(broker: str) -> DummyRunner:
        reached["factory"] = True
        return DummyRunner()

    monkeypatch.setattr(api_server, "_runner_factory", build_runner)
    monkeypatch.setattr("src.trading.service.broker_supports_live_runner", lambda broker: True)
    monkeypatch.setattr("src.live.halt.halt_flag_set", lambda broker=None: False)
    api_server._runner_tasks.clear()

    response = _local_client().post(
        "/live/runner/start",
        headers={
            "Host": "attacker.example:8899",
            "Origin": "http://attacker.example:8899",
            "Content-Type": "application/json",
        },
        json={"broker": "robinhood", "session_id": "proof-session"},
    )

    assert response.status_code == 403
    assert reached["factory"] is False
    assert "robinhood" not in api_server._runner_tasks


def test_allowed_loopback_host_can_start_live_runner_dev_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allowed local hosts preserve the loopback dev-mode runner control path."""
    monkeypatch.setattr(api_server, "_active_mandate_state", lambda broker: SimpleNamespace(expired=False))

    reached = {"factory": False}

    class DummyRunner:
        async def run_loop(self):
            return None

    def build_runner(broker: str) -> DummyRunner:
        reached["factory"] = True
        return DummyRunner()

    monkeypatch.setattr(api_server, "_runner_factory", build_runner)
    monkeypatch.setattr("src.trading.service.broker_supports_live_runner", lambda broker: True)
    monkeypatch.setattr("src.live.halt.halt_flag_set", lambda broker=None: False)
    api_server._runner_tasks.clear()

    response = _local_client().post(
        "/live/runner/start",
        headers={"Host": "127.0.0.1:8899", "Content-Type": "application/json"},
        json={"broker": "robinhood", "session_id": "proof-session"},
    )

    assert response.status_code == 200
    assert reached["factory"] is True
    task = api_server._runner_tasks.pop("robinhood", None)
    if task is not None and not task.done():
        task.cancel()


def test_configured_api_key_required_for_session_event_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _remote_client().get("/sessions/missing/events")

    assert response.status_code == 401


def test_session_event_stream_accepts_query_token_for_browser_eventsource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _remote_client().get("/sessions/missing/events?api_key=secret")

    assert response.status_code in {404, 501}


def test_shell_tools_disabled_for_loopback_api_request_by_default() -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    assert not api_server._shell_tools_enabled_for_request(request)


def test_shell_tools_disabled_for_remote_api_request_by_default() -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.10"))

    assert not api_server._shell_tools_enabled_for_request(request)


def test_shell_tools_api_request_accepts_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    monkeypatch.setenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", "1")

    assert api_server._shell_tools_enabled_for_request(request)


def test_dns_rebound_swarm_run_does_not_enable_shell_tools_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeRuntime:
        def start_run(self, preset_name: str, user_vars: dict, include_shell_tools: bool = False):
            captured["preset_name"] = preset_name
            captured["user_vars"] = user_vars
            captured["include_shell_tools"] = include_shell_tools
            return SimpleNamespace(
                id="swarm-test-no-shell",
                status=SimpleNamespace(value="running"),
                preset_name=preset_name,
            )

    monkeypatch.setattr(api_server, "_get_swarm_runtime", lambda: FakeRuntime())
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _local_client().post(
        "/swarm/runs",
        headers={
            "Host": "attacker.example:8899",
            "Origin": "http://attacker.example:8899",
        },
        json={
            "preset_name": "technical_analysis_panel",
            "user_vars": {"target": "NVDA", "timeframe": "1d"},
        },
    )

    # The rebound-host middleware (#242) rejects the attacker-controlled Host
    # before /swarm/runs runs, so the request never reaches the point where shell
    # tools would be granted — the swarm runtime is never invoked.
    assert response.status_code == 403
    assert "include_shell_tools" not in captured


def test_dns_rebound_session_message_does_not_enable_shell_tools_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeSessionService:
        async def send_message(self, session_id: str, content: str, include_shell_tools: bool = False):
            captured["session_id"] = session_id
            captured["content"] = content
            captured["include_shell_tools"] = include_shell_tools
            return {"message_id": "msg-test", "attempt_id": "attempt-test"}

    monkeypatch.setattr(api_server, "_get_session_service", lambda: FakeSessionService())
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")

    response = _local_client().post(
        "/sessions/abcdef012345/messages",
        headers={
            "Host": "attacker.example:8899",
            "Origin": "http://attacker.example:8899",
        },
        json={"content": "SESSION_DNS_REBIND_PROOF_PAYLOAD"},
    )

    # The rebound-host middleware (#242) rejects the attacker-controlled Host
    # before /sessions/{id}/messages runs, so the session service is never
    # invoked and shell tools can never be granted via a DNS-rebound request.
    assert response.status_code == 403
    assert "include_shell_tools" not in captured


def test_default_cors_origins_are_loopback_only() -> None:
    origins = api_server._parse_cors_origins(None)

    assert origins
    assert "*" not in origins
    assert all(
        origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")
        for origin in origins
    )


def test_cors_origins_reject_credentialed_wildcard() -> None:
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        api_server._parse_cors_origins("https://app.example.com,*")


def test_cors_origins_accept_explicit_remote_origins() -> None:
    origins = api_server._parse_cors_origins(" https://app.example.com,https://admin.example.com ")

    assert origins == ["https://app.example.com", "https://admin.example.com"]


def test_loopback_shutdown_requires_bearer_when_api_key_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loopback alone must not authorize the browser-reachable shutdown action."""
    called: list[bool] = []
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    monkeypatch.setattr(api_server, "_terminate_current_process", lambda: called.append(True))

    response = _local_client().post("/system/shutdown")

    assert response.status_code == 401
    assert called == []


def test_loopback_shutdown_rejects_cross_site_browser_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CORS is not enough; unsafe cross-site browser POSTs must be rejected."""
    called: list[bool] = []
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    monkeypatch.setattr(api_server, "_terminate_current_process", lambda: called.append(True))

    response = _local_client().post(
        "/system/shutdown",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 403
    assert called == []


def test_loopback_shutdown_accepts_valid_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[bool] = []
    monkeypatch.setenv("API_AUTH_KEY", "secret")
    monkeypatch.setattr(api_server, "_API_KEY", "secret")
    monkeypatch.setattr(api_server, "_terminate_current_process", lambda: called.append(True))

    response = _local_client().post(
        "/system/shutdown",
        headers={"Authorization": "Bearer secret", "Origin": "http://127.0.0.1:8899"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "shutting-down"
    assert called == [True]


# ============================================================================
# Path-parameter validation (run_id / session_id)
# ============================================================================


@pytest.mark.parametrize(
    "value",
    [
        # Real formats produced by the codebase.
        "20260105_120342_12_a1b2c3",            # state.create_run_dir
        "swarm-20260105_120342-a1b2c3",         # swarm presets.run_id
        "abcdef012345",                         # session_id (uuid.uuid4().hex[:12])
        "run-1",
        "A" * 128,
    ],
)
def test_validate_path_param_accepts_known_good_values(value: str) -> None:
    api_server._validate_path_param(value, "run_id")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "..",
        "../etc",
        "foo/bar",
        "foo\\bar",
        "foo bar",
        "foo.bar",             # dot is not in the safe class
        "foo\n",
        "foo\r",
        "foo\t",
        "foo\x00bar",
        "A" * 129,
    ],
)
def test_validate_path_param_rejects_traversal_inputs(value: str) -> None:
    with pytest.raises(api_server.HTTPException) as excinfo:
        api_server._validate_path_param(value, "run_id")

    assert excinfo.value.status_code == 400
    assert "run_id" in excinfo.value.detail


def test_get_run_code_rejects_dot_run_id() -> None:
    response = _local_client().get("/runs/../code")

    # Either rejected at routing (404) or by the validator (400). Both are safe;
    # what we forbid is reading code from outside RUNS_DIR.
    assert response.status_code in {400, 404}


def test_get_run_pine_rejects_traversal_run_id() -> None:
    response = _local_client().get("/runs/foo.bar/pine")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid run_id"


def test_get_run_pine_rejects_url_encoded_newline_run_id() -> None:
    response = _local_client().get("/runs/foo%0A/pine")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid run_id"


def test_get_run_result_rejects_traversal_run_id() -> None:
    response = _local_client().get("/runs/foo.bar")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid run_id"


def test_session_endpoints_reject_traversal_session_id() -> None:
    client = _local_client()

    cases = [
        ("get", "/sessions/foo.bar", None),
        ("delete", "/sessions/foo.bar", None),
        ("patch", "/sessions/foo.bar", {"title": "x"}),
        ("post", "/sessions/foo.bar/messages", {"content": "x"}),
        ("get", "/sessions/foo.bar/messages", None),
        ("post", "/sessions/foo.bar/cancel", None),
        ("post", "/sessions/foo.bar/goal", {"objective": "x", "criteria": ["y"]}),
        ("get", "/sessions/foo.bar/goal", None),
        (
            "post",
            "/sessions/foo.bar/goal/evidence",
            {"goal_id": "goal_123", "expected_goal_id": "goal_123", "text": "x"},
        ),
    ]
    for method, path, body in cases:
        kwargs = {"json": body} if body is not None else {}
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 400, f"{method.upper()} {path} should be rejected"
        assert response.json()["detail"] == "invalid session_id"


def test_session_event_stream_rejects_traversal_session_id() -> None:
    response = _local_client().get("/sessions/foo.bar/events")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid session_id"


def test_swarm_run_endpoints_reject_traversal_run_id() -> None:
    client = _local_client()

    for method, path in (
        ("get", "/swarm/runs/foo.bar"),
        ("get", "/swarm/runs/foo.bar/events"),
        ("post", "/swarm/runs/foo.bar/cancel"),
        ("post", "/swarm/runs/foo.bar/retry"),
    ):
        response = getattr(client, method)(path)
        assert response.status_code == 400, f"{method.upper()} {path} should be rejected"
        assert response.json()["detail"] == "invalid run_id"
