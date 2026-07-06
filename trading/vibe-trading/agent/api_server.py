#!/usr/bin/env python3
"""Vibe-Trading API Server - RESTful API for finance research and backtesting.

V5: ReAct Agent + async /run + CORS env + SSE tool events.
"""

from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
import logging
import os
import re
import signal
import time
import csv
import uuid
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Security, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from cli._version import __version__ as APP_VERSION
from src.goal.context import default_goal_criteria
from src.ui_services import build_run_analysis, load_run_context

# UTF-8 on Windows
import sys as _sys
for _s in ("stdout", "stderr"):
    _r = getattr(getattr(_sys, _s, None), "reconfigure", None)
    if callable(_r):
        _r(encoding="utf-8", errors="replace")

RUNS_DIR = Path(__file__).resolve().parent / "runs"
SESSIONS_DIR = Path(__file__).resolve().parent / "sessions"
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
AGENT_DIR = Path(__file__).resolve().parent
ENV_PATH = AGENT_DIR / ".env"
ENV_EXAMPLE_PATH = AGENT_DIR / ".env.example"

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
_UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

console = Console()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class Artifact(BaseModel):
    """Artifact file metadata."""
    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    type: str = Field(..., description="File type: csv, json, txt, etc.")
    size: int = Field(..., description="Size in bytes")
    exists: bool = Field(..., description="Whether the file exists")


class BacktestMetrics(BaseModel):
    """Backtest summary metrics."""
    model_config = {"extra": "allow"}

    final_value: float = Field(..., description="Ending portfolio value")
    total_return: float = Field(..., description="Total return")
    annual_return: float = Field(..., description="Annualized return")
    max_drawdown: float = Field(..., description="Max drawdown")
    sharpe: float = Field(..., description="Sharpe ratio")
    win_rate: float = Field(..., description="Win rate")
    trade_count: int = Field(..., description="Number of trades")



class RAGSelection(BaseModel):
    """RAG routing result."""
    selected_api: str = Field(..., description="Selected API code")
    selected_name: str = Field(..., description="Selected API name")
    selected_score: float = Field(..., description="Match score")


class RunInfo(BaseModel):
    """Compact run row for list views."""
    run_id: str
    status: str
    created_at: str
    prompt: Optional[str] = None
    total_return: Optional[float] = None
    sharpe: Optional[float] = None
    codes: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class RunResponse(BaseModel):
    """API response payload for a single run."""

    status: str = Field(..., description="Run status: success, failed, aborted")
    run_id: str = Field(..., description="Run identifier")
    elapsed_seconds: float = Field(..., description="Execution time in seconds")
    reason: Optional[str] = Field(None, description="Failure reason when available")

    planner_output: Optional[Dict[str, Any]] = Field(None, description="Planner output")
    strategy_spec: Optional[Dict[str, Any]] = Field(None, description="Strategy specification")
    rag_selection: Optional[RAGSelection] = Field(None, description="Selected RAG metadata")

    metrics: Optional[BacktestMetrics] = Field(None, description="Backtest metrics")
    artifacts: List[Artifact] = Field(default_factory=list, description="Run artifacts")
    run_card: Optional[Dict[str, Any]] = Field(None, description="Trust Layer run card payload")
    llm_usage: Optional[Dict[str, Any]] = Field(None, description="Provider-reported AgentLoop usage summary")

    equity_curve: Optional[List[Dict[str, Any]]] = Field(None, description="Equity preview")
    trade_log: Optional[List[Dict[str, Any]]] = Field(None, description="Trade preview")

    artifacts_equity_csv: Optional[List[Dict[str, Any]]] = Field(None, description="Full equity rows")
    artifacts_metrics_csv: Optional[List[Dict[str, Any]]] = Field(None, description="Full metrics rows")
    artifacts_trades_csv: Optional[List[Dict[str, Any]]] = Field(None, description="Full trade rows")
    validation: Optional[Dict[str, Any]] = Field(None, description="Statistical validation results")

    run_directory: str = Field(..., description="Run directory path")
    run_stage: Optional[str] = Field(None, description="UI-facing run stage")
    run_context: Optional[Dict[str, Any]] = Field(None, description="Normalized request context")
    price_series: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Grouped OHLC series")
    indicator_series: Optional[Dict[str, Dict[str, List[Dict[str, Any]]]]] = Field(
        None,
        description="Grouped indicator overlays",
    )
    trade_markers: Optional[List[Dict[str, Any]]] = Field(None, description="Trade markers for charts")
    run_logs: Optional[List[Dict[str, Any]]] = Field(None, description="Structured stdout/stderr lines")


class HealthResponse(BaseModel):
    """Health check payload."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(..., description="Server timestamp")


class LLMProviderOption(BaseModel):
    """Supported LLM provider metadata for the settings UI."""

    name: str
    label: str
    api_key_env: Optional[str] = None
    base_url_env: str
    default_model: str
    default_base_url: str
    api_key_required: bool = True
    auth_type: str = "api_key"
    login_command: Optional[str] = None


class LLMSettingsResponse(BaseModel):
    """Current LLM runtime settings."""

    provider: str
    model_name: str
    base_url: str
    api_key_env: Optional[str] = None
    api_key_configured: bool
    api_key_hint: Optional[str] = None
    api_key_required: bool
    temperature: float
    timeout_seconds: int
    max_retries: int
    reasoning_effort: str
    sse_timeout_seconds: int
    env_path: str
    providers: List[LLMProviderOption]


class UpdateLLMSettingsRequest(BaseModel):
    """Update LLM settings persisted to agent/.env."""

    provider: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    clear_api_key: bool = False
    temperature: float = 0.0
    timeout_seconds: int = Field(120, ge=1, le=3600)
    max_retries: int = Field(2, ge=0, le=20)
    reasoning_effort: Optional[str] = None


class DataSourceSettingsResponse(BaseModel):
    """Current data source credential settings."""

    tushare_token_configured: bool
    tushare_token_hint: Optional[str] = None
    baostock_supported: bool
    baostock_installed: bool
    baostock_message: str
    env_path: str


class UpdateDataSourceSettingsRequest(BaseModel):
    """Update project-local data source credentials."""

    tushare_token: Optional[str] = None
    clear_tushare_token: bool = False


# ---- V4 Session Models ----

class CreateSessionRequest(BaseModel):
    """Create session request body."""
    title: str = Field("", description="Session title")
    config: Optional[Dict[str, Any]] = Field(None, description="Session config")


class SessionResponse(BaseModel):
    """Session record."""
    session_id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    last_attempt_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Send chat message: natural-language strategy description."""
    content: str = Field(..., description="Natural language strategy description", min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Stored chat message."""
    message_id: str
    session_id: str
    role: str
    content: str
    created_at: str
    linked_attempt_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateGoalRequest(BaseModel):
    """Create or replace a finance research goal."""

    objective: str = Field(..., min_length=1, max_length=5000)
    criteria: List[str] = Field(default_factory=list)
    ui_summary: str = ""
    protocol: str = "thesis_review"
    risk_tier: str = "research_general"
    token_budget: Optional[int] = Field(None, ge=1)
    turn_budget: Optional[int] = Field(None, ge=1)
    time_budget_seconds: Optional[int] = Field(None, ge=1)


class UpdateGoalRequest(BaseModel):
    """Edit mutable finance research goal fields."""

    goal_id: str = Field(..., min_length=1)
    expected_goal_id: str = Field(..., min_length=1)
    objective: Optional[str] = Field(None, min_length=1, max_length=5000)
    ui_summary: Optional[str] = Field(None, max_length=500)


class AddGoalEvidenceRequest(BaseModel):
    """Append evidence to a finance research goal."""

    goal_id: str = Field(..., min_length=1)
    expected_goal_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=10000)
    criterion_id: Optional[str] = None
    claim_id: Optional[str] = None
    evidence_type: str = "evidence"
    tool_call_id: Optional[str] = None
    run_id: Optional[str] = None
    source_provider: Optional[str] = None
    source_type: Optional[str] = None
    source_uri: Optional[str] = None
    symbol_universe: List[str] = Field(default_factory=list)
    benchmark: List[str] = Field(default_factory=list)
    timeframe: Optional[str] = None
    method: Optional[str] = None
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    artifact_path: Optional[str] = None
    artifact_hash: Optional[str] = None
    data_as_of: Optional[str] = None
    confidence: Optional[str] = None
    caveat: Optional[str] = None
    contradicts_claim_ids: List[str] = Field(default_factory=list)


class GoalSnapshotResponse(BaseModel):
    """Finance research goal snapshot."""

    goal: Dict[str, Any]
    claims: List[Dict[str, Any]]
    criteria: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    evidence_count: int = 0


class AddGoalEvidenceResponse(BaseModel):
    """Response after appending goal evidence."""

    evidence: Dict[str, Any]
    snapshot: GoalSnapshotResponse


class GoalAuditRowRequest(BaseModel):
    """One criterion row for goal status audits."""

    criterion_id: str = Field(..., min_length=1)
    result: str = Field(..., min_length=1)
    evidence_ids: List[str] = Field(default_factory=list)
    notes: str = ""


class UpdateGoalStatusRequest(BaseModel):
    """Update a finance research goal status."""

    goal_id: str = Field(..., min_length=1)
    expected_goal_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    audit: List[GoalAuditRowRequest] = Field(default_factory=list)
    recap: Optional[str] = None


class UpdateGoalStatusResponse(BaseModel):
    """Response after changing a goal status."""

    goal: Dict[str, Any]
    snapshot: GoalSnapshotResponse


class UpdateGoalResponse(BaseModel):
    """Response after editing a goal."""

    goal: Dict[str, Any]
    snapshot: GoalSnapshotResponse


# ---- Live trading channel: consent commit + kill switch ----


class CommitMandateRequest(BaseModel):
    """Surface-originated mandate commit (Consent §1 / §3).

    This is the ONLY write path that activates a live-trading mandate. It is a
    privileged HTTP action the user surface sends on an explicit click/keypress
    — NOT a tool the agent model can call. ``consent_ack`` MUST be ``true``.
    """

    broker: str = Field(..., min_length=1, max_length=64)
    proposal_id: str = Field(..., pattern=r"^mp_[0-9a-f]{32}$")
    selected_ordinal: int = Field(..., ge=1, le=10)
    adjustments: Optional[Dict[str, Any]] = None
    consent_ack: bool = Field(..., description="Explicit affirmative; must be true")
    session_id: Optional[str] = None
    account_ref: str = Field("", max_length=128)
    lifetime_days: int = Field(30, ge=1, le=365)


class LiveHaltRequest(BaseModel):
    """Trip or clear the live kill switch (Consent §4).

    Tripping/clearing is a privileged surface action, never an agent tool. When
    ``broker`` is omitted the GLOBAL switch is used (halts every broker).
    """

    broker: Optional[str] = Field(None, max_length=64)
    reason: str = Field("user requested halt", max_length=500)
    session_id: Optional[str] = None


class LiveAuthorizeRequest(BaseModel):
    """Kick off (or describe) the OAuth bootstrap for a live broker (C2).

    Vibe-Trading never holds funds and never operates a venue, so the OAuth
    bootstrap runs through the broker's own user-authorized device flow on the
    client (CLI / desktop MCP), not a server-side redirect. This endpoint is the
    web on-ramp: it tells a Web UI user exactly how to discover/start the flow.
    """

    broker: str = Field(..., min_length=1, max_length=64)


class LiveRunnerControlRequest(BaseModel):
    """Start or stop the persistent live runner for one broker (SPEC §7.5).

    The runner wakes on schedule/market events and trades autonomously inside a
    committed mandate. Starting it is a privileged surface action, never an
    agent tool. A committed, unexpired mandate must already exist.
    """

    broker: str = Field(..., min_length=1, max_length=64)
    session_id: Optional[str] = None


class BrokerAuthState(BaseModel):
    """Per-broker authorization snapshot for ``GET /live/status``."""

    broker: str
    oauth_token_present: bool = Field(..., description="Whether an OAuth token cache exists")
    is_live_broker: bool = Field(..., description="Whether this key is a recognized live broker")


class MandateLimits(BaseModel):
    """Flattened active-mandate limits surfaced to the UI (Mandate layer a/b)."""

    max_order_notional_usd: float
    max_total_exposure_usd: float
    max_leverage: float
    max_trades_per_day: int
    allowed_instruments: List[str]
    account_funding_usd: float


class ActiveMandateState(BaseModel):
    """Active-mandate snapshot with the expiry countdown (SPEC §9 dec. 2)."""

    broker: str
    account_ref: str
    created_at: str
    expires_at: str
    expires_in_seconds: Optional[int] = Field(
        None, description="Seconds until expiry; negative when already expired"
    )
    expired: bool
    limits: MandateLimits


class RunnerLivenessState(BaseModel):
    """Runner liveness snapshot via the §7.5 liveness contract."""

    broker: str
    alive: bool
    last_tick: Optional[float] = Field(None, description="Unix epoch of last heartbeat tick")
    last_tick_age_seconds: Optional[float] = None


class LiveBrokerStatus(BaseModel):
    """Combined live-channel status for a single broker."""

    auth: BrokerAuthState
    mandate: Optional[ActiveMandateState] = None
    runner: RunnerLivenessState
    halted: bool = Field(..., description="Per-broker OR global kill switch is tripped")


class LiveStatusResponse(BaseModel):
    """Top-level live-channel status (C2)."""

    global_halted: bool = Field(..., description="Whether the GLOBAL kill switch is tripped")
    brokers: List[LiveBrokerStatus]



# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Vibe-Trading API",
    description="Vibe-Trading API: natural-language finance research, backtesting, and swarm workflows",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

_DEFAULT_LOOPBACK_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "[::1]",
    # Starlette/FastAPI TestClient default host; included so unit tests exercise
    # the API without having to override Host on every request.
    "testserver",
})


def _parse_cors_origins(raw: Optional[str]) -> List[str]:
    """Parse CORS origins and reject credentialed wildcard configuration.

    Args:
        raw: Comma-separated CORS origins from ``CORS_ORIGINS``. ``None`` or a
            blank value uses the loopback development defaults.

    Returns:
        Explicit CORS origins accepted by the API server.

    Raises:
        RuntimeError: If a wildcard origin is configured while credentials are
            enabled.
    """
    if raw is None or not raw.strip():
        return list(_DEFAULT_CORS_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS='*' is not allowed while credentials are enabled; "
            "configure explicit Web UI origins instead."
        )
    return origins


def _parse_extra_loopback_hosts(raw: Optional[str]) -> set[str]:
    """Return additional trusted Host names for loopback API traffic."""
    if raw is None or not raw.strip():
        return set()
    return {host.strip().lower().rstrip(".") for host in raw.split(",") if host.strip()}


_EXTRA_LOOPBACK_HOSTS = _parse_extra_loopback_hosts(os.getenv("API_ALLOWED_HOSTS"))


def _host_without_port(host: str) -> str:
    """Normalize a Host header to a lowercase hostname without a port."""
    value = host.strip().lower().rstrip(".")
    if not value:
        return ""
    if value.startswith("["):
        end = value.find("]")
        if end != -1:
            return value[: end + 1]
        return value
    if value.count(":") == 1:
        return value.rsplit(":", 1)[0]
    return value


def _is_allowed_loopback_host(host: str) -> bool:
    """Return whether ``host`` is allowed for loopback-trusted API requests."""
    normalized = _host_without_port(host)
    return normalized in _DEFAULT_LOOPBACK_HOSTS or normalized in _EXTRA_LOOPBACK_HOSTS


# CORS: override with CORS_ORIGINS (comma-separated explicit origins)
_CORS_ORIGINS = _parse_cors_origins(os.getenv("CORS_ORIGINS"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _reject_untrusted_loopback_host(request: Request, call_next):
    """Block DNS-rebinding Host headers before loopback auth bypasses run."""
    if _is_local_client(request) and not _is_allowed_loopback_host(request.headers.get("host", "")):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Untrusted local API host"},
        )
    return await call_next(request)


# ----------------------------------------------------------------------------
# SPA deep-link fallback
# ----------------------------------------------------------------------------
# A handful of API routes share their path with frontend SPA routes (e.g.
# ``/runs/{id}`` and ``/correlation``). Because FastAPI matches registered
# routes before the static SPA mount, a browser that refreshes or bookmarks
# one of these URLs would receive JSON (or 401/422) instead of the SPA shell.
# The middleware below serves ``frontend/dist/index.html`` when the request
# clearly came from a browser (``Accept`` contains ``text/html``); programmatic
# clients are routed to the real API handler as before.
#
# Patterns are written narrowly so the SPA shell only shadows paths that
# actually correspond to frontend pages. In particular ``/runs/{id}`` is
# the RunDetail page, but ``/runs/{id}/code`` and ``/runs/{id}/pine`` are
# API-only endpoints with no SPA route — using a broad ``/runs/`` prefix
# here would incorrectly hijack those when the browser sets ``Accept:
# text/html`` (e.g. a user pasting the URL into the address bar).

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_SPA_HTML_EXACT_PATHS: frozenset[str] = frozenset({"/correlation"})
# Each regex matches a complete request path. Trailing slash optional.
_SPA_HTML_PATH_REGEX: tuple[re.Pattern[str], ...] = (
    # ``/runs/{run_id}`` — RunDetail page. Excludes ``/runs/{id}/code``,
    # ``/runs/{id}/pine`` (API only) and ``/runs`` (collection endpoint).
    re.compile(r"^/runs/[^/]+/?$"),
)


def _is_spa_html_route(path: str) -> bool:
    """Return True when ``path`` corresponds to a frontend SPA page that
    shadows an API endpoint and should fall back to ``index.html`` on
    browser navigation."""
    if path in _SPA_HTML_EXACT_PATHS:
        return True
    return any(pattern.match(path) for pattern in _SPA_HTML_PATH_REGEX)


@app.middleware("http")
async def _spa_html_deep_link_fallback(request: Request, call_next):
    """Serve ``frontend/dist/index.html`` when a browser navigates directly to
    an SPA path that also exists as an API endpoint.

    Conflicts: ``/runs/{id}`` (RunDetail page vs API) and ``/correlation``
    (Correlation page vs API). Programmatic clients (``Accept: */*`` or
    ``application/json``) still hit the real API handler.
    """
    if request.method == "GET":
        accept = request.headers.get("accept", "")
        if "text/html" in accept and _is_spa_html_route(request.url.path):
            index = _FRONTEND_DIST / "index.html"
            if index.exists():
                return FileResponse(str(index))
    return await call_next(request)


@app.on_event("startup")
async def _run_startup_preflight() -> None:
    """Run preflight checks on server startup."""
    from src.preflight import run_preflight

    run_preflight(console)
    _start_scheduled_research_executor()


@app.on_event("shutdown")
async def _stop_scheduled_research_on_shutdown() -> None:
    """Stop the scheduled research executor on server shutdown."""
    await _stop_scheduled_research_executor()


# ============================================================================
# API Key Authentication
# ============================================================================

_security = HTTPBearer(auto_error=False)
_API_KEY = os.getenv("API_AUTH_KEY")
_SHELL_TOOLS_ENV = "VIBE_TRADING_ENABLE_SHELL_TOOLS"
_DOCKER_LOOPBACK_ENV = "VIBE_TRADING_TRUST_DOCKER_LOOPBACK"


def _configured_api_key() -> str:
    """Return the current API auth key, if configured."""
    return os.getenv("API_AUTH_KEY") or _API_KEY or ""


async def require_auth(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Security(_security),
) -> None:
    """Validate Bearer token for sensitive API endpoints.

    Args:
        request: Incoming HTTP request.
        cred: HTTP Bearer credentials extracted from the Authorization header.

    Raises:
        HTTPException: 403 when dev-mode auth is reached from a non-local client.
        HTTPException: 401 when API_AUTH_KEY is set but the token is missing or wrong.
    """
    _validate_api_auth(request=request, cred=cred)


async def require_event_stream_auth(
    request: Request,
    api_key: Optional[str] = Query(None),
    cred: Optional[HTTPAuthorizationCredentials] = Security(_security),
) -> None:
    """Validate auth for browser EventSource streams.

    Native EventSource cannot send custom Authorization headers, so event
    stream endpoints may accept the API key from the query string. Normal JSON
    endpoints must continue to use Bearer auth only.

    Args:
        request: Incoming HTTP request.
        api_key: Optional query-string API key for EventSource clients.
        cred: HTTP Bearer credentials extracted from the Authorization header.
    """
    _validate_api_auth(request=request, cred=cred, query_api_key=api_key, allow_query=True)


def _auth_credential_from_header_or_query(
    cred: Optional[HTTPAuthorizationCredentials],
    query_api_key: Optional[str],
    *,
    allow_query: bool,
) -> str:
    """Return the supplied API credential from the permitted source."""
    if cred and cred.credentials:
        return cred.credentials
    if allow_query and query_api_key:
        return query_api_key
    return ""


def _is_loopback_origin(origin: str) -> bool:
    """Return whether a browser Origin header names a loopback web UI."""
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _origin_matches_request_host(origin: str, request: Request) -> bool:
    """Return whether ``origin`` is the same site serving this request."""
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False

    origin_host = parsed.hostname.rstrip(".").lower()
    origin_port = parsed.port
    request_host = _host_without_port(request.headers.get("host", ""))
    if origin_host != request_host:
        return False

    if origin_port is None:
        origin_port = 443 if parsed.scheme == "https" else 80
    request_port = request.url.port
    if request_port is None:
        request_port = 443 if request.url.scheme == "https" else 80
    return origin_port == request_port


def _reject_cross_site_browser_request(request: Request) -> None:
    """Reject unsafe browser requests from untrusted cross-site origins.

    CORS protects response reads, not blind form/fetch side effects. Keep local
    CLI/curl clients and same-origin browser UI deployments working while
    refusing browser-originated cross-site POSTs to local control-plane actions
    such as shutdown.
    """
    sec_fetch_site = request.headers.get("sec-fetch-site", "").lower()
    if sec_fetch_site == "cross-site":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-site request denied")

    origin = request.headers.get("origin")
    if origin and not (_is_loopback_origin(origin) or _origin_matches_request_host(origin, request)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-site request denied")


def _require_shutdown_authorization(
    *,
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials],
) -> None:
    """Authorize the local shutdown control-plane action.

    Loopback peer IP alone is not enough for this browser-reachable, destructive
    action. When API_AUTH_KEY is configured, require the Bearer token even for
    loopback requests; otherwise preserve local dev-mode shutdown for direct
    loopback clients while rejecting cross-site browser requests.
    """
    _reject_cross_site_browser_request(request)
    api_key = _configured_api_key()
    if api_key:
        token = _auth_credential_from_header_or_query(cred, None, allow_query=False)
        if not token or not hmac.compare_digest(token, api_key):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return
    if not _is_local_client(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API_AUTH_KEY is required for non-local API access",
        )


_SAFE_BROWSER_METHODS = {"GET", "HEAD", "OPTIONS"}


def _validate_api_auth(
    *,
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials],
    query_api_key: Optional[str] = None,
    allow_query: bool = False,
) -> None:
    """Validate configured auth, preserving loopback-only dev mode."""
    # CORS protects response reads, not blind side effects. Reject unsafe
    # browser-originated cross-site requests before honoring loopback dev-mode
    # trust, otherwise a malicious page can drive local POST/PUT/DELETE routes.
    if request.method.upper() not in _SAFE_BROWSER_METHODS:
        _reject_cross_site_browser_request(request)

    # Loopback clients are always trusted, even when API_AUTH_KEY is set.
    # The key only gates non-local (LAN/remote) access.
    if _is_local_client(request):
        return

    api_key = _configured_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API_AUTH_KEY is required for non-local API access",
        )

    token = _auth_credential_from_header_or_query(cred, query_api_key, allow_query=allow_query)
    if not token or not hmac.compare_digest(token, api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _is_local_client(request: Request) -> bool:
    """Return whether the request originates from a loopback client."""
    host = request.client.host if request.client else ""
    if host in {"localhost", "testclient"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    if ip.is_loopback:
        return True
    return _trusted_docker_loopback_ip(ip)


def _env_flag_enabled(name: str) -> bool:
    """Return whether a boolean environment flag is enabled."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _default_gateway_ips() -> set[ipaddress.IPv4Address]:
    """Return IPv4 default gateway addresses from Linux procfs."""
    gateways: set[ipaddress.IPv4Address] = set()
    try:
        lines = Path("/proc/net/route").read_text(encoding="utf-8").splitlines()
    except OSError:
        return gateways

    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 3 or fields[1] != "00000000":
            continue
        try:
            raw = int(fields[2], 16).to_bytes(4, byteorder="little")
            gateways.add(ipaddress.IPv4Address(raw))
        except ValueError:
            continue
    return gateways


def _trusted_docker_loopback_ip(ip: ipaddress._BaseAddress) -> bool:
    """Return whether an IP is the trusted Docker host gateway.

    Docker Desktop presents host requests to a container as the bridge gateway
    instead of 127.0.0.1. This escape hatch is safe only when the published
    port is bound to host loopback, so the official compose file enables it
    together with a 127.0.0.1 port binding.
    """
    if not isinstance(ip, ipaddress.IPv4Address):
        return False
    if not _env_flag_enabled(_DOCKER_LOOPBACK_ENV):
        return False
    return ip in _default_gateway_ips()


def _env_shell_tools_enabled() -> bool:
    """Return whether server-side shell tools are explicitly enabled."""
    return _env_flag_enabled(_SHELL_TOOLS_ENV)


def _shell_tools_enabled_for_request(request: Request) -> bool:
    """Return whether this API request may expose shell tools to the agent."""
    # Shell-capable tools execute commands on the host as the API process user.
    # Do not infer that privilege from peer IP alone: browser DNS rebinding can
    # make attacker-controlled pages appear as loopback clients. Operators who
    # intentionally want API-started agents or swarm workers to receive shell
    # tools must opt in explicitly.
    return _env_shell_tools_enabled()


async def require_local_or_auth(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Security(_security),
) -> None:
    """Protect settings access when dev-mode auth is disabled.

    If API_AUTH_KEY is configured, require the bearer token. If not, allow only
    loopback clients so an API server bound to 0.0.0.0 cannot accept remote
    credential reads or writes in dev mode.
    """
    if _configured_api_key():
        await require_auth(request, cred)
        return
    if not _is_local_client(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Settings access requires API_AUTH_KEY or a local loopback client",
        )


async def require_settings_write_auth(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Security(_security),
) -> None:
    """Require explicit authorization before changing credential-routing settings.

    Settings writes can redirect stored provider credentials to a different
    endpoint. When an API key is configured, loopback peer IP alone is not a
    sufficient user-intent signal because a browser can reach local APIs after
    DNS rebinding.
    """
    api_key = _configured_api_key()
    if api_key:
        token = _auth_credential_from_header_or_query(cred, None, allow_query=False)
        if not token or not hmac.compare_digest(token, api_key):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return

    if not _is_local_client(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Settings writes require API_AUTH_KEY or a local loopback client",
        )


# ============================================================================
# Workflow Factory
# ============================================================================

# ============================================================================
# Helper Functions
# ============================================================================

LLM_PROVIDER_CONFIG_PATH = AGENT_DIR / "src" / "providers" / "llm_providers.json"


def _load_llm_providers() -> List[LLMProviderOption]:
    """Load provider metadata from JSON so additions stay data-driven."""
    try:
        raw = json.loads(LLM_PROVIDER_CONFIG_PATH.read_text(encoding="utf-8"))
        providers = [LLMProviderOption(**item) for item in raw]
    except Exception as exc:
        raise RuntimeError(f"Failed to load LLM provider config: {LLM_PROVIDER_CONFIG_PATH}") from exc

    seen: set[str] = set()
    for provider in providers:
        if provider.name in seen:
            raise RuntimeError(f"Duplicate LLM provider name: {provider.name}")
        seen.add(provider.name)
    if not providers:
        raise RuntimeError("LLM provider config must not be empty")
    return providers


LLM_PROVIDERS = _load_llm_providers()
LLM_PROVIDER_BY_NAME = {provider.name: provider for provider in LLM_PROVIDERS}
LLM_REASONING_EFFORTS = {"", "low", "medium", "high", "max"}
LLM_API_KEY_PLACEHOLDERS = {"", "sk-or-v1-your-key-here", "sk-xxx", "xxx", "gsk_xxx"}
TUSHARE_TOKEN_PLACEHOLDERS = {"", "your-tushare-token"}


def _ensure_agent_env_file() -> Path:
    """Ensure the project-local agent/.env exists."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text("# Created by Vibe-Trading Web UI settings.\n", encoding="utf-8")
    return ENV_PATH


def _strip_env_value(value: str) -> str:
    """Remove basic dotenv quotes and inline comments."""
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def _read_env_values(path: Path) -> Dict[str, str]:
    """Read active KEY=value entries from a dotenv file."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = _strip_env_value(value)
    return values


def _read_settings_env_values() -> Dict[str, str]:
    """Read settings without creating agent/.env.

    Prefer the user's active agent/.env. If it does not exist yet, fall back to
    agent/.env.example for display defaults only.
    """
    if ENV_PATH.exists():
        return _read_env_values(ENV_PATH)
    if ENV_EXAMPLE_PATH.exists():
        return _read_env_values(ENV_EXAMPLE_PATH)
    return {}


def _project_relative_path(path: Path) -> str:
    """Return a project-relative display path without leaking an absolute path."""
    try:
        return path.resolve().relative_to(AGENT_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.name


def _format_env_value(value: str) -> str:
    """Format a dotenv value without allowing multiline injection."""
    if "\n" in value or "\r" in value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Environment values cannot contain newlines")
    value = value.strip()
    if not value:
        return ""
    if any(ch.isspace() for ch in value) or "#" in value:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def _write_env_values(path: Path, updates: Dict[str, str]) -> None:
    """Upsert active dotenv values while preserving comments and ordering."""
    _ensure_agent_env_file()
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    for index, raw in enumerate(lines):
        stripped = raw.lstrip()
        is_comment = stripped.startswith("#")
        candidate = stripped[1:].lstrip() if is_comment else stripped
        if "=" not in candidate:
            continue
        key = candidate.split("=", 1)[0].strip()
        if key in updates and key not in seen:
            lines[index] = f"{key}={_format_env_value(updates[key])}"
            seen.add(key)
    missing = [key for key in updates if key not in seen]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# Updated from Web UI")
        for key in missing:
            lines.append(f"{key}={_format_env_value(updates[key])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_configured_secret(value: str, placeholders: set[str]) -> bool:
    """Return True when a secret is set and not a documented placeholder."""
    normalized = value.strip().strip('"').strip("'")
    if not normalized:
        return False
    return normalized.lower() not in {placeholder.lower() for placeholder in placeholders}


def _coerce_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_llm_settings_response(values: Optional[Dict[str, str]] = None) -> LLMSettingsResponse:
    """Build the public settings payload from dotenv values."""
    env_values = values if values is not None else _read_settings_env_values()
    provider_name = env_values.get("LANGCHAIN_PROVIDER", "openai").strip().lower()
    provider = LLM_PROVIDER_BY_NAME.get(provider_name, LLM_PROVIDER_BY_NAME["openai"])
    api_key = env_values.get(provider.api_key_env or "", "") if provider.api_key_env else ""
    api_key_configured = _is_configured_secret(api_key, LLM_API_KEY_PLACEHOLDERS)
    api_key_hint = None
    if provider.auth_type == "oauth":
        try:
            from src.providers.openai_codex import get_openai_codex_login_status

            token = get_openai_codex_login_status()
        except Exception:
            token = None
        api_key_configured = bool(token)
        api_key_hint = None
    return LLMSettingsResponse(
        provider=provider.name,
        model_name=env_values.get("LANGCHAIN_MODEL_NAME", provider.default_model),
        base_url=env_values.get(provider.base_url_env, provider.default_base_url),
        api_key_env=provider.api_key_env,
        api_key_configured=api_key_configured,
        api_key_hint=api_key_hint,
        api_key_required=provider.api_key_required,
        temperature=_coerce_float(env_values.get("LANGCHAIN_TEMPERATURE", "0.0"), 0.0),
        timeout_seconds=_coerce_int(env_values.get("TIMEOUT_SECONDS", "120"), 120),
        max_retries=_coerce_int(env_values.get("MAX_RETRIES", "2"), 2),
        reasoning_effort=env_values.get("LANGCHAIN_REASONING_EFFORT", "").strip().lower(),
        sse_timeout_seconds=_coerce_int(env_values.get("VIBE_TRADING_SSE_TIMEOUT", "90"), 90),
        env_path=_project_relative_path(ENV_PATH),
        providers=LLM_PROVIDERS,
    )


def _baostock_supported() -> bool:
    """Check whether the project has a BaoStock loader implementation."""
    loader_dir = AGENT_DIR / "backtest" / "loaders"
    return any((loader_dir / name).exists() for name in ("baostock.py", "baostock_loader.py"))


def _baostock_installed() -> bool:
    """Check whether the optional BaoStock package is importable."""
    import importlib.util

    return importlib.util.find_spec("baostock") is not None


def _build_data_source_settings_response(values: Optional[Dict[str, str]] = None) -> DataSourceSettingsResponse:
    """Build the public data source settings payload."""
    env_values = values if values is not None else _read_settings_env_values()
    token = env_values.get("TUSHARE_TOKEN", "")
    token_configured = _is_configured_secret(token, TUSHARE_TOKEN_PLACEHOLDERS)
    supported = _baostock_supported()
    installed = _baostock_installed()
    if supported:
        baostock_message = "BaoStock loader is available."
    elif installed:
        baostock_message = "BaoStock package is installed, but this project has no BaoStock loader."
    else:
        baostock_message = "No BaoStock loader is registered in this project."
    return DataSourceSettingsResponse(
        tushare_token_configured=token_configured,
        tushare_token_hint=None,
        baostock_supported=supported,
        baostock_installed=installed,
        baostock_message=baostock_message,
        env_path=_project_relative_path(ENV_PATH),
    )


def _sync_runtime_env(provider: LLMProviderOption, updates: Dict[str, str]) -> None:
    """Apply saved LLM settings to the running API process."""
    for key, value in updates.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

    if provider.api_key_env:
        key_value = os.environ.get(provider.api_key_env, "")
        if _is_configured_secret(key_value, LLM_API_KEY_PLACEHOLDERS):
            os.environ["OPENAI_API_KEY"] = key_value
        else:
            os.environ.pop("OPENAI_API_KEY", None)
    elif provider.auth_type == "oauth":
        os.environ.pop("OPENAI_API_KEY", None)
    else:
        os.environ["OPENAI_API_KEY"] = "ollama"

    base_url = os.environ.get(provider.base_url_env, "")
    if base_url:
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_BASE_URL"] = base_url
    else:
        os.environ.pop("OPENAI_API_BASE", None)
        os.environ.pop("OPENAI_BASE_URL", None)


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON from disk if present."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _load_csv_to_dict(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load CSV rows into a list of dictionaries."""
    try:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
        if limit is not None:
            rows = rows[:limit]
        return rows
    except Exception:
        return []



def _build_response_from_run_dir(
    run_dir: Path,
    elapsed: float,
    *,
    include_analysis: bool = False,
    chart_symbol: Optional[str] = None,
    chart_payload: str = "full",
    chart_symbols_out: Optional[List[str]] = None,
) -> RunResponse:
    """Build a run response from a persisted run directory."""
    run_id = run_dir.name

    response = RunResponse(
        status="unknown",
        run_id=run_id,
        elapsed_seconds=elapsed,
        run_directory=str(run_dir),
    )

    state_data = _load_json_file(run_dir / "state.json")
    if state_data:
        state_status = str(state_data.get("status") or "").lower()
        if state_status == "success":
            response.status = "success"
        elif state_status == "failed":
            response.status = "failed"
            response.reason = state_data.get("reason", "")
        else:
            response.status = state_status or "unknown"
    else:
        response.status = "unknown"

    planner_path = run_dir / "planner_output.json"
    response.planner_output = _load_json_file(planner_path)

    design_path = run_dir / "design_spec.json"
    response.strategy_spec = _load_json_file(design_path)

    rag_path = run_dir / "rag_metadata.json"
    rag_data = _load_json_file(rag_path)
    if rag_data:
        response.rag_selection = RAGSelection(
            selected_api=rag_data.get("selected_api") or rag_data.get("api_code", ""),
            selected_name=rag_data.get("selected_name") or rag_data.get("api_name", ""),
            selected_score=float(rag_data.get("selected_score") or rag_data.get("score", 0.0)),
        )

    metrics_path = run_dir / "artifacts" / "metrics.csv"
    if metrics_path.exists():
        metrics_dict_list = _load_csv_to_dict(metrics_path, limit=1)
        if metrics_dict_list:
            row = metrics_dict_list[0]
            try:
                # Pass ALL CSV columns to BacktestMetrics (extra="allow")
                parsed: dict = {}
                for k, v in row.items():
                    if not k or not v:
                        continue
                    try:
                        parsed[k] = int(float(v)) if k == "trade_count" or k == "max_consecutive_loss" else float(v)
                    except (ValueError, TypeError):
                        continue
                if "final_value" in parsed:
                    response.metrics = BacktestMetrics(**parsed)
            except (ValueError, TypeError):
                pass


    artifacts_dir = run_dir / "artifacts"
    if artifacts_dir.exists():
        for file_path in artifacts_dir.iterdir():
            if file_path.is_file():
                file_type = file_path.suffix.lstrip(".")
                response.artifacts.append(
                    Artifact(
                        name=file_path.name,
                        path=str(file_path),
                        type=file_type if file_type else "unknown",
                        size=file_path.stat().st_size,
                        exists=True,
                    )
                )

    equity_path = run_dir / "artifacts" / "equity.csv"
    if equity_path.exists():
        response.artifacts_equity_csv = _load_csv_to_dict(equity_path)

    metrics_csv_path = run_dir / "artifacts" / "metrics.csv"
    if metrics_csv_path.exists():
        response.artifacts_metrics_csv = _load_csv_to_dict(metrics_csv_path)

    run_card_path = run_dir / "run_card.json"
    if run_card_path.exists():
        try:
            response.run_card = json.loads(run_card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    llm_usage_path = run_dir / "llm_usage.json"
    if llm_usage_path.exists():
        try:
            response.llm_usage = json.loads(llm_usage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    trades_path = run_dir / "artifacts" / "trades.csv"
    if trades_path.exists():
        response.artifacts_trades_csv = _load_csv_to_dict(trades_path)

    validation_path = run_dir / "artifacts" / "validation.json"
    if validation_path.exists():
        try:
            response.validation = json.loads(validation_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    if response.artifacts_equity_csv:
        filtered_equity = []
        for row in response.artifacts_equity_csv[:1000]:
            filtered_row: Dict[str, Any] = {}
            if "timestamp" in row:
                filtered_row["time"] = row["timestamp"]
            if "equity" in row:
                filtered_row["equity"] = row["equity"]
            if "drawdown" in row:
                filtered_row["drawdown"] = row["drawdown"]
            filtered_equity.append(filtered_row)
        response.equity_curve = filtered_equity

    if response.artifacts_trades_csv:
        response.trade_log = response.artifacts_trades_csv[:500]

    if include_analysis:
        analysis = build_run_analysis(
            run_dir,
        symbols=[chart_symbol] if chart_symbol else None,
        include_payload=chart_payload != "summary" or bool(chart_symbol),
        include_symbol_list=chart_symbols_out is not None,
    )
        if chart_symbols_out is not None:
            chart_symbols_out.extend(analysis.get("chart_symbols") or [])
        response.run_stage = analysis.get("run_stage")
        response.run_context = analysis.get("run_context")
        response.price_series = analysis.get("price_series")
        response.indicator_series = analysis.get("indicator_series")
        response.trade_markers = analysis.get("trade_markers")
        response.run_logs = analysis.get("run_logs")

    return response


def _run_response_payload(response: RunResponse) -> Dict[str, Any]:
    """Return a JSON-ready payload for opt-in run response variants."""
    return response.model_dump(mode="json")


# ============================================================================
# Path-parameter validation
# ============================================================================

# ``run_id`` and ``session_id`` flow directly into filesystem paths
# (``RUNS_DIR / run_id`` etc.). Restrict to a safe character class so that
# values like ``..`` or ``foo/../bar`` cannot escape the parent directory.
_SAFE_PATH_PARAM_RE = __import__("re").compile(r"^[A-Za-z0-9_-]{1,128}$")


def _validate_path_param(value: str, kind: str) -> None:
    """Reject path parameters that could escape the parent directory.

    Args:
        value: User-supplied path-parameter value.
        kind: Parameter name, used in the error detail.

    Raises:
        HTTPException: 400 when ``value`` does not match the safe character
            class, mirroring the existing ``_SHADOW_ID_RE`` check.
    """
    if not _SAFE_PATH_PARAM_RE.fullmatch(value or ""):
        raise HTTPException(status_code=400, detail=f"invalid {kind}")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/runs/{run_id}/code", dependencies=[Depends(require_auth)])
async def get_run_code(run_id: str):
    """Return strategy source files for a run.

    Args:
        run_id: Run identifier.

    Returns:
        Map filename -> source text.
    """
    _validate_path_param(run_id, "run_id")
    run_dir = RUNS_DIR / run_id / "code"
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Code directory for run {run_id} not found")
    result = {}
    for f in ["signal_engine.py"]:
        p = run_dir / f
        if p.exists():
            result[f] = p.read_text(encoding="utf-8")
    return result


@app.get("/runs/{run_id}/pine", dependencies=[Depends(require_auth)])
async def get_run_pine(run_id: str):
    """Return Pine Script file for a run.

    Args:
        run_id: Run identifier.

    Returns:
        Object with pine script content and exists flag.
    """
    _validate_path_param(run_id, "run_id")
    pine_path = RUNS_DIR / run_id / "artifacts" / "strategy.pine"
    if not pine_path.exists():
        return {"exists": False, "content": None}
    return {
        "exists": True,
        "content": pine_path.read_text(encoding="utf-8"),
    }


@app.get("/runs/{run_id}", response_model=RunResponse, dependencies=[Depends(require_auth)])
async def get_run_result(
    run_id: str,
    chart_symbol: Optional[str] = Query(None, description="Opt in to chart payloads for a single symbol"),
    chart_payload: Optional[str] = Query(
        None,
        description="Optional chart payload mode. Use 'summary' to omit chart rows and trade markers.",
    ),
):
    """Fetch details for a historical run by ``run_id``.

    The default response stays unchanged for existing consumers. Chart-heavy
    optimizations are opt-in via query parameters.
    """
    _validate_path_param(run_id, "run_id")
    if chart_payload not in (None, "summary"):
        raise HTTPException(status_code=400, detail="invalid chart_payload")
    run_dir = RUNS_DIR / run_id

    if not run_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found"
        )

    wants_chart_meta = bool(chart_payload or chart_symbol)
    chart_symbols: List[str] = []
    response = _build_response_from_run_dir(
        run_dir,
        elapsed=0.0,
        include_analysis=True,
        chart_symbol=chart_symbol,
        chart_payload=chart_payload or "full",
        chart_symbols_out=chart_symbols if wants_chart_meta else None,
    )

    if wants_chart_meta:
        payload = _run_response_payload(response)
        payload["chart_symbols"] = chart_symbols
        return JSONResponse(payload)

    return response


@app.get("/runs", response_model=List[RunInfo], dependencies=[Depends(require_auth)])
async def list_runs(limit: int = 20):
    """List recent runs with summary fields."""
    limit = min(max(1, limit), 100)
    runs_dir = RUNS_DIR

    if not runs_dir.exists():
        return []

    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir()],
        key=lambda x: x.name,
        reverse=True
    )

    results = []
    for d in run_dirs[:limit]:
        run_id = d.name

        # Status from state.json or artifacts
        status_val = "unknown"
        state_file = _load_json_file(d / "state.json")
        if state_file:
            status_val = str(state_file.get("status") or "unknown").lower()
        elif (d / "artifacts" / "equity.csv").exists():
            status_val = "success"
        elif (d / "review_report.json").exists():
            status_val = "success"

        # Parse created_at from run_id (YYYYMMDD_HHMMSS or run_YYYYMMDD_HHMMSS)
        created_at = "Unknown"
        if run_id.startswith("run_"):
            parts = run_id.split('_')
            if len(parts) >= 3:
                d_str, t_str = parts[1], parts[2]
                if len(d_str) == 8 and len(t_str) == 6:
                    created_at = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:8]} {t_str[:2]}:{t_str[2:4]}:{t_str[4:6]}"
        elif "_" in run_id:
            parts = run_id.split('_')
            if len(parts) >= 2:
                d_str, t_str = parts[0], parts[1]
                if len(d_str) == 8 and len(t_str) == 6:
                    created_at = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:8]} {t_str[:2]}:{t_str[2:4]}:{t_str[4:6]}"

        if created_at == "Unknown":
            mtime = datetime.fromtimestamp(d.stat().st_mtime)
            created_at = mtime.strftime("%Y-%m-%d %H:%M:%S")

        prompt = None
        req_file = d / "req.json"
        planner_file = d / "planner_output.json"
        if req_file.exists():
            try:
                req_data = json.loads(req_file.read_text(encoding="utf-8"))
                prompt = req_data.get("prompt")
            except (json.JSONDecodeError, OSError):
                pass

        if not prompt and planner_file.exists():
            try:
                planner_data = json.loads(planner_file.read_text(encoding="utf-8"))
                prompt = planner_data.get("user_goal") or planner_data.get("goal")
            except (json.JSONDecodeError, OSError):
                pass

        if not prompt:
            prompt_file = d / "user_prompt.txt"
            if prompt_file.exists():
                prompt = prompt_file.read_text(encoding="utf-8").strip()

        total_return = None
        sharpe = None
        metrics_file = d / "artifacts" / "metrics.csv"
        if metrics_file.exists():
            try:
                import csv
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total_return = float(row.get('total_return', 0) or 0)
                        sharpe = float(row.get('sharpe', 0) or 0)
                        break
            except (OSError, ValueError):
                pass

        run_context = load_run_context(d)
        results.append(RunInfo(
            run_id=run_id,
            status=status_val,
            created_at=created_at,
            prompt=prompt or "Manual Analysis",
            total_return=total_return,
            sharpe=sharpe,
            codes=run_context.get("codes") or [],
            start_date=run_context.get("start_date"),
            end_date=run_context.get("end_date"),
        ))

    return results


@app.get(
    "/settings/llm",
    response_model=LLMSettingsResponse,
    dependencies=[Depends(require_local_or_auth)],
)
async def get_llm_settings():
    """Return project-local LLM settings for the Web UI."""
    return _build_llm_settings_response()


@app.put("/settings/llm", response_model=LLMSettingsResponse, dependencies=[Depends(require_settings_write_auth)])
async def update_llm_settings(payload: UpdateLLMSettingsRequest):
    """Persist project-local LLM settings and update the running process."""
    provider_name = payload.provider.strip().lower()
    provider = LLM_PROVIDER_BY_NAME.get(provider_name)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported LLM provider")

    model_name = payload.model_name.strip()
    if not model_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model name is required")

    if payload.temperature < 0 or payload.temperature > 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Temperature must be between 0 and 2")

    reasoning_effort = (payload.reasoning_effort or "").strip().lower()
    if reasoning_effort not in LLM_REASONING_EFFORTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reasoning effort must be low, medium, high, or max")

    current_values = _read_settings_env_values()
    base_url = (payload.base_url if payload.base_url is not None else provider.default_base_url).strip()
    if provider.auth_type == "oauth":
        try:
            from src.providers.openai_codex import validate_codex_base_url

            base_url = validate_codex_base_url(base_url)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    updates: Dict[str, str] = {
        "LANGCHAIN_PROVIDER": provider.name,
        "LANGCHAIN_MODEL_NAME": model_name,
        provider.base_url_env: base_url,
        "LANGCHAIN_TEMPERATURE": str(payload.temperature),
        "TIMEOUT_SECONDS": str(payload.timeout_seconds),
        "MAX_RETRIES": str(payload.max_retries),
    }
    if reasoning_effort or "LANGCHAIN_REASONING_EFFORT" in current_values:
        updates["LANGCHAIN_REASONING_EFFORT"] = reasoning_effort

    if provider.api_key_env:
        if payload.clear_api_key:
            updates[provider.api_key_env] = ""
        elif payload.api_key is not None and payload.api_key.strip():
            api_key = payload.api_key.strip()
            updates[provider.api_key_env] = api_key if _is_configured_secret(api_key, LLM_API_KEY_PLACEHOLDERS) else ""
        elif provider.api_key_env in current_values and _is_configured_secret(
            current_values[provider.api_key_env],
            LLM_API_KEY_PLACEHOLDERS,
        ):
            updates[provider.api_key_env] = current_values[provider.api_key_env]
    elif payload.clear_api_key:
        os.environ.pop("OPENAI_API_KEY", None)

    _write_env_values(ENV_PATH, updates)
    _sync_runtime_env(provider, updates)
    return _build_llm_settings_response(_read_env_values(ENV_PATH))


@app.get(
    "/settings/data-sources",
    response_model=DataSourceSettingsResponse,
    dependencies=[Depends(require_local_or_auth)],
)
async def get_data_source_settings():
    """Return project-local data source credentials for the Web UI."""
    return _build_data_source_settings_response()


@app.put(
    "/settings/data-sources",
    response_model=DataSourceSettingsResponse,
    dependencies=[Depends(require_settings_write_auth)],
)
async def update_data_source_settings(payload: UpdateDataSourceSettingsRequest):
    """Persist project-local data source credentials and update the running process."""
    current_values = _read_settings_env_values()
    updates: Dict[str, str] = {}

    if payload.clear_tushare_token:
        updates["TUSHARE_TOKEN"] = ""
    elif payload.tushare_token is not None and payload.tushare_token.strip():
        updates["TUSHARE_TOKEN"] = payload.tushare_token.strip()
    elif "TUSHARE_TOKEN" in current_values:
        updates["TUSHARE_TOKEN"] = current_values["TUSHARE_TOKEN"]

    if updates:
        _write_env_values(ENV_PATH, updates)
        token = updates.get("TUSHARE_TOKEN", "").strip()
        if _is_configured_secret(token, TUSHARE_TOKEN_PLACEHOLDERS):
            os.environ["TUSHARE_TOKEN"] = token
        else:
            os.environ.pop("TUSHARE_TOKEN", None)

    return _build_data_source_settings_response(_read_env_values(ENV_PATH))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe."""
    return HealthResponse(
        status="healthy",
        service="Vibe-Trading API",
        timestamp=datetime.now().isoformat()
    )


@app.get("/correlation")
async def get_correlation_matrix(
    codes: str = Query(..., description="Comma-separated asset codes, e.g. BTC-USDT,ETH-USDT,SPY"),
    days: int = Query(90, description="Lookback window in days", ge=7, le=365),
    method: str = Query("pearson", description="Correlation method: pearson or spearman"),
):
    """Compute cross-asset correlation matrix from daily returns.

    Fetches price data for each code via available data loaders,
    computes pairwise correlation of daily returns over the lookback window.
    """
    from backtest.correlation import compute_correlation_matrix

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if len(code_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 asset codes required")
    if len(code_list) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 assets per request")
    if method not in ("pearson", "spearman"):
        raise HTTPException(status_code=400, detail="method must be 'pearson' or 'spearman'")

    try:
        result = compute_correlation_matrix(codes=code_list, days=days, method=method)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Correlation computation failed: {exc}")


def _terminate_current_process() -> None:
    """Stop the current API process after the response has been sent."""
    time.sleep(0.25)
    os.kill(os.getpid(), signal.SIGTERM)


@app.post("/system/shutdown")
async def shutdown_local_api(
    background_tasks: BackgroundTasks,
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Security(_security),
):
    """Shut down the local API server after explicit local authorization."""
    _require_shutdown_authorization(request=request, cred=cred)
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local access only")

    background_tasks.add_task(_terminate_current_process)
    return {
        "status": "shutting-down",
        "service": "Vibe-Trading API",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/skills")
async def list_skills():
    """List registered skills (name and description)."""
    from src.agent.skills import SkillsLoader

    loader = SkillsLoader()
    return [
        {
            "name": s.name,
            "description": s.description,
        }
        for s in loader.skills
    ]


@app.get("/api")
async def api_info():
    """Service metadata."""
    return {
        "service": "Vibe-Trading API",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Session API
# ============================================================================

_session_service = None
_goal_store = None


def _get_session_service():
    """Lazy-init session service when ENABLE_SESSION_RUNTIME=true."""
    global _session_service
    if _session_service is not None:
        return _session_service

    if os.getenv("ENABLE_SESSION_RUNTIME", "true").lower() != "true":
        return None

    import asyncio
    from src.session.store import SessionStore
    from src.session.events import EventBus
    from src.session.service import SessionService

    store = SessionStore(base_dir=SESSIONS_DIR)
    event_bus = EventBus()

    try:
        loop = asyncio.get_event_loop()
        event_bus.set_loop(loop)
    except RuntimeError:
        pass

    _session_service = SessionService(
        store=store,
        event_bus=event_bus,
        runs_dir=RUNS_DIR,
    )
    return _session_service


def _get_goal_store():
    """Return the shared finance goal store."""
    global _goal_store
    if _goal_store is None:
        from src.goal import GoalStore

        _goal_store = GoalStore()
    return _goal_store


def _get_existing_session_or_404(session_id: str):
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return svc, session


@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_auth)])
async def create_session(request: CreateSessionRequest):
    """Create a chat session."""
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    session = svc.create_session(title=request.title, config=request.config)
    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_attempt_id=session.last_attempt_id,
    )


@app.get("/sessions", response_model=List[SessionResponse], dependencies=[Depends(require_auth)])
async def list_sessions(limit: int = Query(50, ge=1, le=200)):
    """List sessions."""
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    sessions = svc.list_sessions(limit=limit)
    return [
        SessionResponse(
            session_id=s.session_id,
            title=s.title,
            status=s.status.value,
            created_at=s.created_at,
            updated_at=s.updated_at,
            last_attempt_id=s.last_attempt_id,
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=SessionResponse, dependencies=[Depends(require_auth)])
async def get_session(session_id: str):
    """Get one session by id."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_attempt_id=session.last_attempt_id,
    )


@app.post(
    "/sessions/{session_id}/goal",
    response_model=GoalSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_auth)],
)
async def create_session_goal(session_id: str, req: CreateGoalRequest):
    """Create or replace the current finance research goal for a session."""
    _validate_path_param(session_id, "session_id")
    svc, _session = _get_existing_session_or_404(session_id)
    from src.goal import RiskTier

    criteria = [item.strip() for item in req.criteria if item.strip()]
    if not criteria:
        criteria = default_goal_criteria()
    try:
        risk_tier = RiskTier(req.risk_tier)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid risk_tier: {req.risk_tier}") from exc
    if risk_tier is RiskTier.LIVE_TRADING_OR_EXECUTION:
        raise HTTPException(status_code=400, detail="live trading or execution goals are not supported")

    goal_store = _get_goal_store()
    try:
        goal = goal_store.replace_goal(
            session_id=session_id,
            objective=req.objective,
            criteria=criteria,
            ui_summary=req.ui_summary,
            source="api",
            protocol=req.protocol,
            risk_tier=risk_tier,
            token_budget=req.token_budget,
            turn_budget=req.turn_budget,
            time_budget_seconds=req.time_budget_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    snapshot = goal_store.get_goal_snapshot(goal.goal_id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Goal created but could not be reloaded")
    svc.event_bus.emit(session_id, "goal.created", {"goal": snapshot["goal"]})
    return snapshot


@app.get(
    "/sessions/{session_id}/goal",
    response_model=GoalSnapshotResponse,
    dependencies=[Depends(require_auth)],
)
async def get_session_goal(session_id: str):
    """Return the current finance research goal snapshot for a session."""
    _validate_path_param(session_id, "session_id")
    _get_existing_session_or_404(session_id)
    snapshot = _get_goal_store().get_current_snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No current goal")
    return snapshot


@app.patch(
    "/sessions/{session_id}/goal",
    response_model=UpdateGoalResponse,
    dependencies=[Depends(require_auth)],
)
async def update_session_goal(session_id: str, req: UpdateGoalRequest):
    """Edit the current finance research goal without replacing the session."""
    _validate_path_param(session_id, "session_id")
    svc, _session = _get_existing_session_or_404(session_id)
    from src.goal import StaleGoalError

    if req.objective is None and req.ui_summary is None:
        raise HTTPException(status_code=400, detail="objective or ui_summary is required")

    goal_store = _get_goal_store()
    try:
        goal = goal_store.update_goal(
            session_id=session_id,
            goal_id=req.goal_id,
            expected_goal_id=req.expected_goal_id,
            objective=req.objective,
            ui_summary=req.ui_summary,
        )
    except StaleGoalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    snapshot = goal_store.get_goal_snapshot(goal.goal_id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Goal snapshot could not be reloaded")
    svc.event_bus.emit(session_id, "goal.updated", {"goal": snapshot["goal"], "snapshot": snapshot})
    return {"goal": snapshot["goal"], "snapshot": snapshot}


@app.post(
    "/sessions/{session_id}/goal/evidence",
    response_model=AddGoalEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_auth)],
)
async def add_session_goal_evidence(session_id: str, req: AddGoalEvidenceRequest):
    """Append traceable evidence to the current finance research goal."""
    _validate_path_param(session_id, "session_id")
    svc, _session = _get_existing_session_or_404(session_id)
    from dataclasses import asdict
    from src.goal import EvidenceInput, StaleGoalError

    goal_store = _get_goal_store()
    try:
        evidence = goal_store.append_evidence(
            session_id=session_id,
            goal_id=req.goal_id,
            expected_goal_id=req.expected_goal_id,
            evidence=EvidenceInput(
                criterion_id=req.criterion_id,
                claim_id=req.claim_id,
                evidence_type=req.evidence_type,
                text=req.text,
                tool_call_id=req.tool_call_id,
                run_id=req.run_id,
                source_provider=req.source_provider,
                source_type=req.source_type,
                source_uri=req.source_uri,
                symbol_universe=req.symbol_universe,
                benchmark=req.benchmark,
                timeframe=req.timeframe,
                method=req.method,
                assumptions=req.assumptions,
                artifact_path=req.artifact_path,
                artifact_hash=req.artifact_hash,
                data_as_of=req.data_as_of,
                confidence=req.confidence,
                caveat=req.caveat,
                contradicts_claim_ids=req.contradicts_claim_ids,
            ),
        )
    except StaleGoalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    snapshot = goal_store.get_goal_snapshot(req.goal_id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Goal snapshot could not be reloaded")
    svc.event_bus.emit(
        session_id,
        "goal.evidence",
        {"evidence": asdict(evidence), "goal_id": req.goal_id},
    )
    return {"evidence": asdict(evidence), "snapshot": snapshot}


@app.patch(
    "/sessions/{session_id}/goal/status",
    response_model=UpdateGoalStatusResponse,
    dependencies=[Depends(require_auth)],
)
async def update_session_goal_status(session_id: str, req: UpdateGoalStatusRequest):
    """Update the current finance research goal status."""
    _validate_path_param(session_id, "session_id")
    svc, _session = _get_existing_session_or_404(session_id)
    from src.goal import AuditRow, GoalStatus, StaleGoalError

    try:
        next_status = GoalStatus(req.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid goal status: {req.status}") from exc

    goal_store = _get_goal_store()
    try:
        goal = goal_store.update_status(
            session_id=session_id,
            goal_id=req.goal_id,
            expected_goal_id=req.expected_goal_id,
            status=next_status,
            audit=[
                AuditRow(
                    criterion_id=row.criterion_id,
                    result=row.result,
                    evidence_ids=row.evidence_ids,
                    notes=row.notes,
                )
                for row in req.audit
            ],
            recap=req.recap,
        )
    except StaleGoalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    snapshot = goal_store.get_goal_snapshot(goal.goal_id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Goal snapshot could not be reloaded")
    svc.event_bus.emit(session_id, "goal.updated", {"goal": snapshot["goal"], "snapshot": snapshot})
    return {"goal": snapshot["goal"], "snapshot": snapshot}


@app.delete("/sessions/{session_id}", dependencies=[Depends(require_auth)])
async def delete_session(session_id: str):
    """Delete a session."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    deleted = svc.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    _get_goal_store().delete_session_goals(session_id)
    return {"status": "deleted", "session_id": session_id}


class UpdateSessionRequest(BaseModel):
    """Session update fields."""
    title: Optional[str] = None


@app.patch("/sessions/{session_id}", dependencies=[Depends(require_auth)])
async def update_session(session_id: str, req: UpdateSessionRequest):
    """Update session fields (e.g. title)."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    session = svc.store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    if req.title is not None:
        session.title = req.title
    from datetime import datetime
    session.updated_at = datetime.now().isoformat()
    svc.store.update_session(session)
    return {"status": "updated", "session_id": session_id}


@app.post("/sessions/{session_id}/messages", dependencies=[Depends(require_auth)])
async def send_message(session_id: str, payload: SendMessageRequest, http_request: Request):
    """Send a user message and start the agent loop (natural language strategy)."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    try:
        result = await svc.send_message(
            session_id=session_id,
            content=payload.content,
            include_shell_tools=_shell_tools_enabled_for_request(http_request),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/sessions/{session_id}/cancel", dependencies=[Depends(require_auth)])
async def cancel_session(session_id: str):
    """Cancel the in-flight agent loop for this session."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    cancelled = svc.cancel_current(session_id)
    if not cancelled:
        return {"status": "no_active_loop"}
    return {"status": "cancelled"}


@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse], dependencies=[Depends(require_auth)])
async def get_messages(session_id: str, limit: int = Query(100, ge=1, le=1000)):
    """List messages for a session."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    messages = svc.get_messages(session_id, limit=limit)
    return [
        MessageResponse(
            message_id=m.message_id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            linked_attempt_id=m.linked_attempt_id,
            metadata=m.metadata if m.metadata else None,
        )
        for m in messages
    ]


@app.get("/sessions/{session_id}/events", dependencies=[Depends(require_event_stream_auth)])
async def session_events(
    session_id: str,
    request: Request,
    last_event_id: Optional[str] = Query(None, alias="Last-Event-ID"),
    replay: Optional[str] = Query(None),
):
    """SSE stream for agent events."""
    _validate_path_param(session_id, "session_id")
    svc = _get_session_service()
    if not svc:
        raise HTTPException(status_code=501, detail="Session runtime not enabled")
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    header_id = request.headers.get("Last-Event-ID")
    event_id = header_id or last_event_id
    replay_active = (replay or "").lower() == "active"
    replay_all = False
    if replay_active and not event_id and session.last_attempt_id:
        attempt = svc.store.get_attempt(session_id, session.last_attempt_id)
        attempt_status = getattr(attempt.status, "value", attempt.status) if attempt else None
        replay_all = attempt_status == "running"

    async def event_generator():
        async for event in svc.event_bus.subscribe(
            session_id,
            last_event_id=event_id,
            replay_all=replay_all,
        ):
            if await request.is_disconnected():
                break
            yield event.to_sse()
            relayed = _mandate_proposal_frame_from_tool_result(event)
            if relayed is not None:
                yield relayed
            live_action = _live_action_frame_from_tool_result(event)
            if live_action is not None:
                yield live_action

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# File Upload
# ============================================================================

_BLOCKED_UPLOAD_EXT = {
    # binaries / executables we should never accept
    ".exe", ".msi", ".bat", ".cmd", ".com", ".scr", ".app", ".dmg",
    ".so", ".dll", ".dylib",
    # executable-adjacent source, shell, config, and template files
    ".py", ".pyw", ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".yaml", ".yml", ".j2", ".jinja", ".jinja2", ".template",
    # archives — don't auto-extract; user can unpack locally
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz",
}

_BLOCKED_UPLOAD_NAMES = {
    "dockerfile",
    "containerfile",
}


_SHADOW_ID_RE = __import__("re").compile(r"^shadow_[0-9a-f]{8}$")


@app.get("/shadow-reports/{shadow_id}", dependencies=[Depends(require_auth)])
async def get_shadow_report(shadow_id: str, format: str = "html"):
    """Serve a rendered Shadow Account report (HTML by default, PDF if available).

    Reports live under ``~/.vibe-trading/shadow_reports/<shadow_id>.{html,pdf}``.
    """
    if not _SHADOW_ID_RE.match(shadow_id):
        raise HTTPException(status_code=400, detail="invalid shadow_id")
    if format not in ("html", "pdf"):
        raise HTTPException(status_code=400, detail="format must be html or pdf")

    reports_dir = Path.home() / ".vibe-trading" / "shadow_reports"
    path = reports_dir / f"{shadow_id}.{format}"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Shadow report not found: {shadow_id}.{format}")

    media_type = "text/html; charset=utf-8" if format == "html" else "application/pdf"
    # Inline so browsers render HTML/PDF directly instead of forcing download.
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{shadow_id}.{format}"'},
    )


@app.post("/upload", dependencies=[Depends(require_auth)])
async def upload_file(file: UploadFile):
    """Upload any document or data file (max 50MB).

    Accepts most common formats: PDF, Word, Excel, PowerPoint, images,
    CSV/TSV, plain text, JSON, and TOML. Executables, executable-adjacent
    source/config/template files, and archives are rejected.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    filename = Path(file.filename).name
    ext = Path(filename).suffix.lower()
    if ext in _BLOCKED_UPLOAD_EXT or filename.lower() in _BLOCKED_UPLOAD_NAMES:
        raise HTTPException(
            status_code=400,
            detail="This file type is not allowed for upload.",
        )

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / safe_name
    total_size = 0

    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as handle:
            while True:
                chunk = await file.read(_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    handle.close()
                    if dest.exists():
                        dest.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (limit {MAX_UPLOAD_SIZE // (1024 * 1024)} MB)",
                    )
                handle.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        if dest.exists():
            dest.unlink()
        raise HTTPException(
            status_code=500,
            detail="Upload failed while storing the file. Please retry or choose a different file.",
        ) from exc
    finally:
        await file.close()

    return {
        "status": "ok",
        "file_path": f"uploads/{safe_name}",
        "filename": filename,
    }


# ============================================================================
# Swarm API
# ============================================================================

_swarm_runtime = None


def _get_swarm_runtime():
    """Lazy-init SwarmRuntime singleton."""
    global _swarm_runtime
    if _swarm_runtime is not None:
        return _swarm_runtime
    from src.config import load_swarm_agent_config
    from src.swarm.store import SwarmStore
    from src.swarm.runtime import SwarmRuntime
    swarm_dir = Path(__file__).resolve().parent / ".swarm" / "runs"
    store = SwarmStore(base_dir=swarm_dir)
    # Boot-time / operator-trusted: REST API callers cannot influence the
    # config path. See docs/2026-05-25_swarm_mcp_tools_roadmap.md.
    agent_config = load_swarm_agent_config()
    _swarm_runtime = SwarmRuntime(store=store, agent_config=agent_config)
    return _swarm_runtime


@app.get("/swarm/presets")
async def list_swarm_presets():
    """List Swarm YAML presets."""
    from src.swarm.presets import list_presets
    return list_presets()


@app.post("/swarm/runs", dependencies=[Depends(require_auth)])
async def create_swarm_run(payload: dict, http_request: Request):
    """Start a swarm run: body must include preset_name and user_vars."""
    runtime = _get_swarm_runtime()
    preset_name = payload.get("preset_name", "")
    user_vars = payload.get("user_vars", {})
    try:
        run = runtime.start_run(
            preset_name,
            user_vars,
            include_shell_tools=_shell_tools_enabled_for_request(http_request),
        )
        return {"id": run.id, "status": run.status.value, "preset_name": run.preset_name}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/swarm/runs", dependencies=[Depends(require_auth)])
async def list_swarm_runs(limit: int = Query(20, ge=1, le=100)):
    """List swarm runs (newest first), reconciled."""
    runtime = _get_swarm_runtime()
    runs = runtime._store.list_runs(limit=limit)
    items = []
    for r in runs:
        # Reconcile each row: a zombie running run will be auto-finalized so
        # the dashboard never shows a permanent "running" stuck row.
        reconciled = runtime._store.reconcile_run(r, write=True)
        items.append(
            {
                "id": reconciled.id,
                "preset_name": reconciled.preset_name,
                "status": reconciled.status.value,
                "is_stale": runtime._store.is_run_stale(reconciled),
                "created_at": reconciled.created_at,
                "completed_at": reconciled.completed_at,
                "task_count": len(reconciled.tasks),
                "completed_count": sum(1 for t in reconciled.tasks if t.status.value == "completed"),
            }
        )
    return items


@app.get("/swarm/runs/{run_id}", dependencies=[Depends(require_auth)])
async def get_swarm_run(run_id: str):
    """Swarm run detail including task statuses (reconciled)."""
    _validate_path_param(run_id, "run_id")
    runtime = _get_swarm_runtime()
    loaded = runtime._store.load_run(run_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run = runtime._store.reconcile_run(loaded, write=True)

    return {
        "id": run.id,
        "preset_name": run.preset_name,
        "status": run.status.value,
        "is_stale": runtime._store.is_run_stale(run),
        "user_vars": run.user_vars,
        "agents": [a.model_dump() for a in run.agents],
        "tasks": [t.model_dump() for t in run.tasks],
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "final_report": run.final_report,
    }


@app.get("/swarm/runs/{run_id}/events", dependencies=[Depends(require_event_stream_auth)])
async def swarm_run_events(run_id: str, request: Request, last_index: int = Query(0, ge=0)):
    """SSE stream for a swarm run."""
    import asyncio

    _validate_path_param(run_id, "run_id")
    runtime = _get_swarm_runtime()

    async def event_stream():
        idx = last_index
        while True:
            if await request.is_disconnected():
                break
            events = runtime._store.read_events(run_id, after_index=idx)
            for evt in events:
                idx += 1
                yield f"id: {idx}\nevent: {evt.type}\ndata: {json.dumps(evt.model_dump(), ensure_ascii=False)}\n\n"
            run = runtime._store.load_run(run_id)
            if run:
                # Reconcile so a zombie running run can still close this SSE
                # stream cleanly — without it, a dead host would keep the
                # stream open forever and block the dashboard's "done" state.
                reconciled = runtime._store.reconcile_run(run, write=True)
                if reconciled.status.value in ("completed", "failed", "cancelled"):
                    yield f"event: done\ndata: {{\"status\": \"{reconciled.status.value}\"}}\n\n"
                    break
            await asyncio.sleep(2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/swarm/runs/{run_id}/cancel", dependencies=[Depends(require_auth)])
async def cancel_swarm_run(run_id: str):
    """Cancel an active swarm run."""
    _validate_path_param(run_id, "run_id")
    runtime = _get_swarm_runtime()
    ok = runtime.cancel_run(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No active run {run_id}")
    return {"status": "cancelled"}


@app.post("/swarm/runs/{run_id}/retry", dependencies=[Depends(require_auth)])
async def retry_swarm_run(run_id: str, http_request: Request):
    """Retry a failed, stale, or cancelled swarm run.

    Creates a new run with the same preset and user_vars as the original.
    """
    _validate_path_param(run_id, "run_id")
    runtime = _get_swarm_runtime()
    loaded = runtime._store.load_run(run_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Reconcile first so a stale "running" run whose host died gets demoted
    # before we gate on status; only a genuinely active run blocks retry.
    from src.swarm.models import RunStatus

    reconciled = runtime._store.reconcile_run(loaded, write=True)
    if reconciled.status == RunStatus.running:
        raise HTTPException(status_code=409, detail="Cannot retry a running run. Cancel it first.")

    try:
        new_run = runtime.start_run(
            reconciled.preset_name,
            reconciled.user_vars or {},
            include_shell_tools=_shell_tools_enabled_for_request(http_request),
        )
        return {"id": new_run.id, "status": new_run.status.value, "preset_name": new_run.preset_name}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Live trading channel — consent commit + kill switch
# ============================================================================
#
# These are the privileged SURFACE actions of the live-trading channel
# (live-trading SPEC, Consent §1/§3/§4). None is an agent tool:
#   - POST /mandate/commit  -> the single mandate writer (commit_mandate)
#   - POST /live/halt       -> trip the kill switch (P5 trip_halt)
#   - POST /live/resume     -> clear the kill switch (P5 clear_halt)
# Each best-effort relays a mandate.committed / live.halted / live.action event
# through the EXISTING session EventBus, so the frontend's already-wired
# /sessions/{id}/events SSE stream reflects the state change. No new bus.


def _emit_live_event(session_id: Optional[str], event_type: str, data: Dict[str, Any]) -> None:
    """Best-effort relay of a live-channel event through the existing bus.

    The event flows out the existing ``/sessions/{session_id}/events`` SSE
    stream. Notifications never gate autonomy (SPEC Consent §5): a relay failure
    or a missing session is swallowed — the state change already happened on disk.

    Args:
        session_id: Target session, or ``None`` to skip relay.
        event_type: SSE event name (``mandate.committed`` / ``live.halted`` /
            ``live.resumed`` / ``live.action``).
        data: JSON-serializable event payload.
    """
    if not session_id:
        return
    try:
        svc = _get_session_service()
        if svc and svc.get_session(session_id):
            svc.event_bus.emit(session_id, event_type, data)
    except Exception:  # pragma: no cover - relay is non-blocking by contract
        logger.debug("live event relay failed for %s/%s", session_id, event_type, exc_info=True)


# ---- C1: propose_mandate_profiles tool_result -> mandate.proposal SSE frame ----
#
# The agent surfaces a proposal by calling the read-only ``propose_mandate_profiles``
# tool whose tool_result JSON body is ``{"type":"mandate.proposal", ...}`` (SPEC
# Consent §1). The CLI / frontend listen for a TOP-LEVEL ``mandate.proposal`` SSE
# event. ``src/agent/loop.py`` only emits a truncated ``tool_result`` event
# (``preview = result[:200]``) and is PROTECTED — we do NOT edit it. Instead this
# open-file SSE seam (TASKS "Remaining integration items" #1, the recommended
# wiring) detects the propose tool's tool_result on the stream, recovers the
# ``proposal_id`` from the preview, reloads the FULL persisted proposal from the
# proposal store (written by the tool before it returned), and emits the
# ``mandate.proposal`` frame. No protected touch.

_PROPOSAL_TOOL_NAME = "propose_mandate_profiles"
_PROPOSAL_ID_RE = re.compile(r'"proposal_id"\s*:\s*"(mp_[0-9a-f]{32})"')


def _load_full_proposal(proposal_id: str) -> Optional[Dict[str, Any]]:
    """Reload a persisted ``mandate.proposal`` payload by id, broker-agnostic.

    The propose tool persists the full proposal under
    ``<runtime_root>/live/<broker>/proposals/<proposal_id>.json`` before
    returning. The SSE ``tool_result`` preview is too short to carry the full
    body, so the relay reloads it from disk. The broker segment is unknown from
    the preview alone, so every broker's proposals directory is searched.

    Args:
        proposal_id: The ``mp_...`` id parsed from the tool_result preview.

    Returns:
        The full proposal dict, or ``None`` when not found / unreadable.
    """
    try:
        from src.live.paths import live_root

        for proposal_path in live_root().glob(f"*/proposals/{proposal_id}.json"):
            try:
                data = json.loads(proposal_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("type") == "mandate.proposal":
                return data
    except Exception:  # pragma: no cover - relay must never break the stream
        logger.debug("mandate.proposal reload failed for %s", proposal_id, exc_info=True)
    return None


def _mandate_proposal_frame_from_tool_result(event: Any) -> Optional[str]:
    """Build a ``mandate.proposal`` SSE frame from a propose-tool tool_result.

    Args:
        event: An ``SSEEvent`` flowing through the session stream.

    Returns:
        A ready-to-yield SSE text frame for the ``mandate.proposal`` event, or
        ``None`` when ``event`` is not a successful propose-tool result or the
        proposal cannot be recovered.
    """
    data = getattr(event, "data", None)
    if getattr(event, "event_type", None) != "tool_result" or not isinstance(data, dict):
        return None
    if data.get("tool") != _PROPOSAL_TOOL_NAME or data.get("status") != "ok":
        return None
    match = _PROPOSAL_ID_RE.search(str(data.get("preview") or ""))
    if not match:
        return None
    proposal = _load_full_proposal(match.group(1))
    if proposal is None:
        return None

    from src.session.events import SSEEvent

    frame = SSEEvent(
        event_type="mandate.proposal",
        data=proposal,
        session_id=getattr(event, "session_id", "") or "",
    )
    return frame.to_sse()


_LIVE_ACTION_ID_RE = re.compile(r'"audit_id"\s*:\s*"(la_[0-9a-zA-Z]+)"')


def _load_live_action_record(audit_id: str) -> Optional[Dict[str, Any]]:
    """Reload a redacted live-action record from the ledger by ``audit_id``.

    The order guard embeds its (already-redacted) audit record under the
    ``live_action`` key of its tool_result, but the SSE ``tool_result`` preview
    is truncated to ~200 chars, so the full record is reloaded from the
    append-only ledger at ``<runtime_root>/live/audit.jsonl``.

    Args:
        audit_id: The ``la_...`` id parsed from the tool_result preview.

    Returns:
        The full redacted live-action record, or ``None`` when not found.
    """
    try:
        from src.live.paths import live_root

        ledger = live_root() / "audit.jsonl"
        if not ledger.exists():
            return None
        for line in reversed(ledger.read_text(encoding="utf-8").splitlines()):
            if audit_id not in line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("audit_id") == audit_id:
                return record
    except Exception:  # pragma: no cover - relay must never break the stream
        logger.debug("live.action reload failed for %s", audit_id, exc_info=True)
    return None


def _live_action_frame_from_tool_result(event: Any) -> Optional[str]:
    """Build a ``live.action`` SSE frame from an order-guard tool_result.

    The order guard stamps a ``live_action`` audit record onto its tool_result
    (and the ledger) for every live order placed/rejected. The interactive agent
    loop only emits a truncated ``tool_result`` event and is PROTECTED, so this
    open-file relay surfaces the live action as a top-level ``live.action`` event
    for the timeline — without touching ``src/agent/loop.py``. (Autonomous-runner
    actions already emit ``live.action`` natively via the runner's event bus.)

    Args:
        event: An ``SSEEvent`` flowing through the session stream.

    Returns:
        A ready-to-yield ``live.action`` SSE frame, or ``None`` when the event is
        not an order-guard result carrying a recoverable live-action record.
    """
    data = getattr(event, "data", None)
    if getattr(event, "event_type", None) != "tool_result" or not isinstance(data, dict):
        return None
    preview = str(data.get("preview") or "")
    if '"live_action"' not in preview:
        return None
    match = _LIVE_ACTION_ID_RE.search(preview)
    if not match:
        return None
    record = _load_live_action_record(match.group(1))
    if record is None:
        return None

    from src.session.events import SSEEvent

    frame = SSEEvent(
        event_type="live.action",
        data=record,
        session_id=getattr(event, "session_id", "") or "",
    )
    return frame.to_sse()


def _fetch_broker_ceilings(broker: str) -> Optional[Dict[str, Any]]:
    """Best-effort fetch of broker-side account ceilings for the commit re-check.

    Reads the broker's ``get_account`` tool and derives an authoritative ceiling
    snapshot (buying power / funding) so the commit-time fit check binds to the
    venue's real limits rather than an agent-proposed number. Returns ``None`` on
    any failure (channel not configured, tool error, fields not recognized) so
    the caller falls back to the proposal's own snapshot — a commit is never
    blocked on a broker read. The exact Robinhood field names are finalized
    post-access (L6); we probe the common ones.

    Args:
        broker: The live-broker key.

    Returns:
        A ceilings dict (canonical keys) or ``None`` to fall back.
    """
    try:
        adapter = _live_broker_adapter(broker)
    except LiveRunnerUnavailable:
        return None
    try:
        result = adapter.call_tool("get_account", {})
    except Exception:  # pragma: no cover - status/commit must never raise here
        logger.debug("broker ceiling fetch failed for %s", broker, exc_info=True)
        return None
    if not isinstance(result, dict) or result.get("status") == "error":
        return None
    payload = result.get("result") if isinstance(result.get("result"), dict) else result
    funding: Optional[float] = None
    for key in ("account_funding_usd", "buying_power", "cash", "portfolio_value", "equity"):
        raw = payload.get(key) if isinstance(payload, dict) else None
        try:
            if raw is not None:
                funding = float(raw)
                break
        except (TypeError, ValueError):
            continue
    if funding is None or funding <= 0:
        return None
    # A single order can never exceed available funding; total exposure is capped
    # at funding for a cash account. Leverage stays at 1.0 unless the broker
    # reports margin (L6). These canonical keys are normalized by commit_mandate.
    return {
        "account_funding_usd": funding,
        "max_order_notional_usd": funding,
        "max_total_exposure_usd": funding,
    }


@app.post("/mandate/commit", dependencies=[Depends(require_auth)])
async def commit_mandate_endpoint(payload: CommitMandateRequest):
    """Commit a user-selected mandate profile — the only mandate write path.

    Calls :func:`src.live.mandate.commit.commit_mandate`, which re-validates the
    proposal is live and the resolved profile still fits the ceilings the user
    saw. Requires ``consent_ack=true`` (rejected otherwise). On success emits a
    ``mandate.committed`` + ``live.action`` event so all surfaces reflect the
    newly active mandate.
    """
    if payload.consent_ack is not True:
        raise HTTPException(status_code=400, detail="consent_ack must be true to commit a mandate")

    from src.live.mandate.commit import CommitError, commit_mandate

    # Prefer broker-DERIVED ceilings over the agent-supplied proposal snapshot:
    # the commit re-check should bind to the venue's real account limits, not a
    # number the model proposed. Best-effort — falls back to the proposal's own
    # ceilings (commit_mandate handles ceilings_ref=None) when the broker channel
    # is unavailable or the read fails (we never block a commit on a broker read).
    broker_ceilings = _fetch_broker_ceilings(payload.broker)

    try:
        result = commit_mandate(
            proposal_id=payload.proposal_id,
            ordinal=payload.selected_ordinal,
            adjustments=payload.adjustments,
            consent_ack=payload.consent_ack,
            broker=payload.broker,
            account_ref=payload.account_ref,
            session_id=payload.session_id,
            ceilings_ref=broker_ceilings,
            lifetime_days=payload.lifetime_days,
        )
    except CommitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _emit_live_event(payload.session_id, "mandate.committed", result)
    _emit_live_event(
        payload.session_id,
        "live.action",
        {"kind": "mandate_committed", "broker": result["broker"], "mandate_id": result["mandate_id"]},
    )
    return result


@app.post("/live/halt", dependencies=[Depends(require_auth)])
async def halt_live_endpoint(payload: LiveHaltRequest):
    """Trip the live kill switch (privileged surface action, Consent §4).

    Writes the HALT sentinel via :func:`src.live.halt.trip_halt`; the
    enforcement gate then rejects every order attempt until resumed. Emits a
    ``live.halted`` event so all surfaces reflect the halted state.
    """
    from src.live.halt import trip_halt

    try:
        path = trip_halt(by="frontend", reason=payload.reason, broker=payload.broker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = {"halted": True, "broker": payload.broker, "reason": payload.reason, "sentinel": str(path)}
    _emit_live_event(payload.session_id, "live.halted", result)
    _emit_live_event(
        payload.session_id,
        "live.action",
        {"kind": "halt_tripped", "broker": payload.broker, "reason": payload.reason},
    )
    return result


@app.post("/live/resume", dependencies=[Depends(require_auth)])
async def resume_live_endpoint(payload: LiveHaltRequest):
    """Clear the live kill switch (privileged surface action, Consent §4).

    Deletes the HALT sentinel via :func:`src.live.halt.clear_halt` (an explicit
    re-enable; never an agent tool). Emits a ``live.resumed`` event.
    """
    from src.live.halt import clear_halt

    try:
        cleared = clear_halt(broker=payload.broker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = {"halted": False, "broker": payload.broker, "cleared": cleared}
    _emit_live_event(payload.session_id, "live.resumed", result)
    _emit_live_event(
        payload.session_id,
        "live.action",
        {"kind": "halt_cleared", "broker": payload.broker, "cleared": cleared},
    )
    return result


# ============================================================================
# Live trading channel — status, authorize on-ramp, runner control (C2 + §7.5)
# ============================================================================
#
# C2 surfaces the dormant-by-default channel state so a user can SEE what is and
# is not authorized before trusting it: per-broker OAuth presence, the active
# mandate with its expiry countdown, runner liveness, and the kill-switch state.
# The runner-control endpoints start/stop the persistent §7.5 runner that trades
# autonomously inside a committed mandate. None of these is an agent tool; they
# are privileged surface actions like /mandate/commit and /live/halt.


def _known_live_brokers() -> List[str]:
    """Return the recognized live-broker keys (SPEC §7.2)."""
    from src.config.schema import LIVE_BROKER_SERVER_KEYS

    return sorted(LIVE_BROKER_SERVER_KEYS)


def _oauth_token_present(broker: str) -> bool:
    """Return whether an OAuth token cache exists for a broker (C2 auth state).

    The token cache lives at ``<runtime_root>/live/<broker>/oauth/`` (0700) and
    is created only when the user OAuth-authorizes the channel. A missing or
    empty directory means the channel is dormant (read-only, no live path).
    """
    try:
        from src.live.paths import broker_dir

        oauth_dir = broker_dir(broker) / "oauth"
        return oauth_dir.is_dir() and any(oauth_dir.iterdir())
    except Exception:  # pragma: no cover - status must never raise
        logger.debug("oauth presence check failed for %s", broker, exc_info=True)
        return False


def _active_mandate_state(broker: str) -> Optional[ActiveMandateState]:
    """Build the active-mandate snapshot for a broker, or ``None`` when absent.

    Reads the committed mandate via the frozen store contract and computes the
    ``expires_at`` countdown (SPEC §9 dec. 2). A mandate whose ``expires_at`` has
    passed is still surfaced, flagged ``expired`` so the UI can prompt re-consent.
    """
    from src.live.mandate.store import load_mandate

    mandate = load_mandate(broker)
    if mandate is None:
        return None

    consent = mandate.consent
    caps = mandate.hard_caps
    expires_in: Optional[int] = None
    expired = False
    try:
        expires_dt = datetime.fromisoformat(consent.expires_at.replace("Z", "+00:00"))
        from datetime import timezone

        now = datetime.now(timezone.utc)
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)
        delta = expires_dt - now
        expires_in = int(delta.total_seconds())
        expired = expires_in <= 0
    except (ValueError, AttributeError):
        logger.debug("could not parse expires_at for %s mandate", broker, exc_info=True)

    return ActiveMandateState(
        broker=broker,
        account_ref=consent.account_ref,
        created_at=consent.created_at,
        expires_at=consent.expires_at,
        expires_in_seconds=expires_in,
        expired=expired,
        limits=MandateLimits(
            max_order_notional_usd=caps.max_order_notional_usd,
            max_total_exposure_usd=caps.max_total_exposure_usd,
            max_leverage=caps.max_leverage,
            max_trades_per_day=caps.max_trades_per_day,
            allowed_instruments=[str(getattr(i, "value", i)) for i in caps.allowed_instruments],
            account_funding_usd=caps.account_funding_usd,
        ),
    )


def _runner_liveness_state(broker: str) -> RunnerLivenessState:
    """Build the runner-liveness snapshot for a broker (SPEC §7.5 contract).

    Uses the §7.5 ``liveness`` module (``is_runner_alive`` / ``last_tick``),
    keyed by broker as the runner id. The module is built concurrently (R1); a
    missing module or any error is treated as "not alive" (fail-safe display).
    """
    alive = False
    tick: Optional[float] = None
    age: Optional[float] = None
    try:
        from src.live.runtime import liveness

        alive = bool(liveness.is_runner_alive(broker))
        raw_tick = liveness.last_tick(broker)
        if raw_tick is not None:
            tick = float(raw_tick)
            age = max(0.0, time.time() - tick)
    except Exception:  # pragma: no cover - liveness module is built concurrently
        logger.debug("runner liveness lookup failed for %s", broker, exc_info=True)

    return RunnerLivenessState(broker=broker, alive=alive, last_tick=tick, last_tick_age_seconds=age)


@app.get("/live/status", response_model=LiveStatusResponse, dependencies=[Depends(require_auth)])
async def live_status_endpoint(broker: Optional[str] = Query(None, max_length=64)):
    """Return live-channel status: auth, active mandate, runner liveness, halt (C2).

    Args:
        broker: Optional single-broker filter. When omitted, every recognized
            live broker is reported.

    Returns:
        A :class:`LiveStatusResponse` with the global kill-switch state and a
        per-broker breakdown so the UI can show exactly what is authorized.
    """
    from src.live.halt import halt_flag_set

    if broker is not None:
        target = broker.strip().lower()
        if not target:
            raise HTTPException(status_code=400, detail="broker must not be blank")
        brokers = [target]
    else:
        brokers = _known_live_brokers()

    known = set(_known_live_brokers())
    statuses: List[LiveBrokerStatus] = []
    for key in brokers:
        statuses.append(
            LiveBrokerStatus(
                auth=BrokerAuthState(
                    broker=key,
                    oauth_token_present=_oauth_token_present(key),
                    is_live_broker=key in known,
                ),
                mandate=_active_mandate_state(key),
                runner=_runner_liveness_state(key),
                halted=halt_flag_set(broker=key),
            )
        )

    return LiveStatusResponse(global_halted=halt_flag_set(broker=None), brokers=statuses)


@app.post("/live/authorize", dependencies=[Depends(require_auth)])
async def live_authorize_endpoint(payload: LiveAuthorizeRequest):
    """Describe the OAuth bootstrap on-ramp for a live broker (C2 web on-ramp).

    Vibe-Trading holds no funds and runs no venue: the OAuth flow happens on the
    broker's own user-authorized device channel (CLI / desktop MCP), never a
    server-side redirect. A Web UI user reaches this endpoint to DISCOVER how to
    start the flow. It performs no authorization itself and never returns a token.
    """
    broker = payload.broker.strip().lower()
    if not broker:
        raise HTTPException(status_code=400, detail="broker must not be blank")
    if broker not in set(_known_live_brokers()):
        raise HTTPException(status_code=400, detail=f"unknown live broker: {broker}")

    from src.trading.service import connector_profile_id_for_broker

    connector_profile = connector_profile_id_for_broker(broker)
    return {
        "broker": broker,
        "connector_profile": connector_profile,
        "oauth_token_present": _oauth_token_present(broker),
        "instruction": (
            f"Run `vibe-trading connector authorize {connector_profile}` "
            "from the device that will hold the broker session. This opens the "
            "broker's own OAuth consent flow; Vibe-Trading never holds funds and "
            "only relays intent once you authorize."
        ),
        "note": (
            "The live channel stays read-only until the OAuth token is present AND a "
            "mandate is committed AND order tools are explicitly enabled."
        ),
    }


# ---- Runner control (SPEC §7.5): start / stop the persistent live runner ----
#
# A LiveRunner (R2 contract: ``LiveRunner(broker)`` with ``run_loop()`` /
# ``run_once()``) is driven in a background task per broker. The factory is
# injectable (``_runner_factory``) so tests stub it with no real agent/broker.
# ``run_loop`` may be sync (long-blocking) or async; both are supported.

_runner_tasks: Dict[str, "asyncio.Task[Any]"] = {}
_runner_factory: Optional[Any] = None


class LiveRunnerUnavailable(RuntimeError):
    """Raised when a live runner cannot be wired (broker not configured/authorized).

    Distinct from a programming error so the start endpoint can map it to a 503
    rather than a 500: the runtime is fine, the broker channel just isn't ready.
    """


def _live_broker_adapter(broker: str) -> Any:
    """Build an ``MCPServerAdapter`` for a live broker from the user-side config.

    Resolves the broker's MCP server entry by config key OR by a live-broker URL
    host (so an aliased key still resolves), mirroring the registry's detection.

    Args:
        broker: The live-broker key, e.g. ``"robinhood"``.

    Returns:
        A constructed :class:`MCPServerAdapter` for the broker's read/write tools.

    Raises:
        LiveRunnerUnavailable: When no MCP server is configured for the broker.
    """
    from src.config.loader import load_agent_config
    from src.tools.mcp import MCPServerAdapter

    try:
        from src.config.schema import is_live_broker_entry
    except Exception:  # pragma: no cover - older schema without URL detection
        is_live_broker_entry = None  # type: ignore[assignment]

    cfg = load_agent_config()
    servers = getattr(cfg, "mcp_servers", {}) or {}
    for name, server_cfg in servers.items():
        is_match = name == broker
        if not is_match and is_live_broker_entry is not None and broker == "robinhood":
            try:
                is_match = is_live_broker_entry(name, server_cfg)
            except Exception:  # pragma: no cover
                is_match = False
        if is_match:
            return MCPServerAdapter(name, server_cfg)
    raise LiveRunnerUnavailable(f"no MCP server configured for live broker {broker!r}")


def _build_live_runner(broker: str) -> Any:
    """Construct a fully-wired ``LiveRunner`` for a broker (SPEC §7.5 R-INT).

    Wires the runner to the real surfaces — the public ``SessionService`` agent
    caller (never the protected loop internals), the broker's READ/WRITE MCP
    tools, the R4 reconciler, the R1 scheduler, and R3 market-hours triggers —
    and injects an audit ``event_callback`` so every autonomous live action is
    broadcast as a ``live.action`` SSE event on the runner's session bus.

    Args:
        broker: The live-broker key.

    Returns:
        A runner object exposing ``run_loop`` / ``run_once`` (R2 contract).

    Raises:
        LiveRunnerUnavailable: When the broker channel is not configured.
    """
    if _runner_factory is not None:
        return _runner_factory(broker)

    from src.live.audit import write_live_action
    from src.live.runtime.reconcile import reconcile
    from src.live.runtime.runner import LiveRunner
    from src.live.runtime.scheduler import Scheduler
    from src.live.runtime.triggers import Trigger
    from src.trading.service import runner_tool_name

    def _tool(operation: str) -> str:
        remote_tool = runner_tool_name(broker, operation)
        if remote_tool is None:
            raise LiveRunnerUnavailable(
                f"live runner for {broker!r} does not define remote tool {operation!r}"
            )
        return remote_tool

    positions_tool = _tool("positions")
    balance_tool = _tool("account")
    open_orders_tool = _tool("orders")
    submit_order_tool = _tool("submit_order")
    cancel_order_tool = _tool("cancel_order")
    adapter = _live_broker_adapter(broker)  # raises LiveRunnerUnavailable if absent

    def _read(remote_tool: str):
        """A zero-arg broker READ callable bound to one remote tool."""
        return lambda: adapter.call_tool(remote_tool, {})

    def _submit(order: Dict[str, Any]) -> Dict[str, Any]:
        # Route the flatten sweep's normalized order to the broker's write tools.
        # Field mapping against the real Robinhood schema is finalized post-access
        # (L6); the action discriminator is broker-agnostic.
        if order.get("action") == "cancel":
            return adapter.call_tool(cancel_order_tool, order)
        return adapter.call_tool(submit_order_tool, order)

    svc = _get_session_service()
    session = svc.create_session(title=f"live-runner:{broker}")
    session_id = session.session_id

    async def _agent_caller(sid: str, prompt: str) -> Dict[str, Any]:
        # Dispatch one autonomous turn through the PUBLIC SessionService entry.
        # The agent then trades within the mandate via the gated order tools.
        return await svc.send_message(sid, prompt)

    def _audit_with_bus(event: Any) -> Dict[str, Any]:
        # Broadcast each live action as a live.action SSE event on the runner's
        # session bus (no protected-loop touch — the runner owns its session).
        return write_live_action(
            event,
            event_callback=lambda etype, record: svc.event_bus.emit(session_id, etype, record),
        )

    # Wire the scheduler's fire callback to the runner's tick. The scheduler is
    # constructed before the runner (it needs on_fire), and the runner needs the
    # scheduler, so late-bind via a holder to break the cycle.
    runner_holder: Dict[str, Any] = {}

    async def _on_fire(_job: Any) -> None:
        runner = runner_holder.get("runner")
        if runner is not None:
            await runner.run_once()

    scheduler = Scheduler(_on_fire)

    runner = LiveRunner(
        broker,
        agent_caller=_agent_caller,
        reconcile_fn=reconcile,
        read_positions=_read(positions_tool),
        read_balance=_read(balance_tool),
        read_open_orders=_read(open_orders_tool),
        submit_fn=_submit,
        write_audit_fn=_audit_with_bus,
        scheduler=scheduler,
        triggers=[Trigger.market("us_equity")],
        session_id=session_id,
    )
    runner_holder["runner"] = runner
    return runner


async def _drive_runner(runner: Any) -> None:
    """Run a runner's ``run_loop`` to completion, sync or async.

    A synchronous ``run_loop`` is offloaded to a worker thread so it does not
    block the event loop; an async ``run_loop`` is awaited directly.
    """
    result = runner.run_loop()
    if asyncio.iscoroutine(result):
        await result
    else:
        await asyncio.get_running_loop().run_in_executor(None, lambda: result)


@app.post("/live/runner/start", dependencies=[Depends(require_auth)])
async def start_runner_endpoint(payload: LiveRunnerControlRequest):
    """Start the persistent live runner for a broker (SPEC §7.5).

    Refuses to start unless a committed, unexpired mandate exists and the kill
    switch is clear — the runner trades autonomously, so it must not start into a
    dead/halted channel. Idempotent: a request for an already-running broker
    returns ``already_running`` without spawning a second task.
    """
    from src.live.halt import halt_flag_set

    broker = payload.broker.strip().lower()
    if not broker:
        raise HTTPException(status_code=400, detail="broker must not be blank")
    from src.trading.service import broker_supports_live_runner

    if not broker_supports_live_runner(broker):
        raise HTTPException(
            status_code=400,
            detail=f"live runner is not supported for {broker}",
        )

    existing = _runner_tasks.get(broker)
    if existing is not None and not existing.done():
        return {"broker": broker, "started": False, "already_running": True}

    mandate = _active_mandate_state(broker)
    if mandate is None:
        raise HTTPException(status_code=409, detail=f"no committed mandate for {broker}")
    if mandate.expired:
        raise HTTPException(status_code=409, detail=f"mandate for {broker} has expired; re-authorize first")
    if halt_flag_set(broker=broker) or halt_flag_set(broker=None):
        raise HTTPException(status_code=409, detail="kill switch is tripped; resume before starting the runner")

    try:
        runner = _build_live_runner(broker)
    except LiveRunnerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"could not construct runner: {exc}") from exc

    task = asyncio.ensure_future(_drive_runner(runner))
    _runner_tasks[broker] = task
    task.add_done_callback(
        lambda t, b=broker: _runner_tasks.pop(b, None) if _runner_tasks.get(b) is t else None
    )

    _emit_live_event(
        payload.session_id,
        "live.action",
        {"kind": "runner_started", "broker": broker},
    )
    return {"broker": broker, "started": True, "already_running": False}


@app.post("/live/runner/stop", dependencies=[Depends(require_auth)])
async def stop_runner_endpoint(payload: LiveRunnerControlRequest):
    """Stop the persistent live runner for a broker (SPEC §7.5).

    Cancels the background task. This does NOT flatten positions — that is the
    preemptive kill switch's job (``/live/halt`` -> flatten); stopping the runner
    simply ceases new autonomous turns. Idempotent for an already-stopped broker.
    """
    broker = payload.broker.strip().lower()
    if not broker:
        raise HTTPException(status_code=400, detail="broker must not be blank")
    from src.trading.service import broker_supports_live_runner

    if not broker_supports_live_runner(broker):
        raise HTTPException(
            status_code=400,
            detail=f"live runner is not supported for {broker}",
        )

    task = _runner_tasks.pop(broker, None)
    if task is None or task.done():
        return {"broker": broker, "stopped": False, "was_running": False}

    task.cancel()
    _emit_live_event(
        payload.session_id,
        "live.action",
        {"kind": "runner_stopped", "broker": broker},
    )
    return {"broker": broker, "stopped": True, "was_running": True}


# ============================================================================
# Alpha Zoo routes (Web UI) — defined in src/api/alpha_routes.py
# ============================================================================

from src.api.alpha_routes import register_alpha_routes  # noqa: E402
register_alpha_routes(app)


# ============================================================================
# Scheduled Research Routes
# ============================================================================
#
# Lightweight CRUD endpoints backed by ScheduledResearchJobStore. The endpoint
# handlers only record and expose jobs; the optional executor lifecycle is
# guarded separately by VIBE_TRADING_ENABLE_SCHEDULER.


_SCHEDULED_RESEARCH_SCHEDULER_ENV = "VIBE_TRADING_ENABLE_SCHEDULER"
_SCHEDULED_RESEARCH_TRUE_VALUES = {"1", "true", "yes", "on"}

_scheduled_research_store: Optional["ScheduledResearchJobStore"] = None
_scheduled_research_executor: Optional["ScheduledResearchExecutor"] = None


def _get_scheduled_research_store() -> "ScheduledResearchJobStore":
    """Return the singleton ScheduledResearchJobStore, creating it on first call."""
    global _scheduled_research_store
    if _scheduled_research_store is None:
        from src.scheduled_research.store import ScheduledResearchJobStore

        _scheduled_research_store = ScheduledResearchJobStore()
    return _scheduled_research_store


def _scheduled_research_scheduler_enabled() -> bool:
    """Return whether scheduled research execution is enabled."""
    return os.getenv(_SCHEDULED_RESEARCH_SCHEDULER_ENV, "").strip().lower() in _SCHEDULED_RESEARCH_TRUE_VALUES


async def _dispatch_scheduled_research_job(job: "ScheduledResearchJob") -> None:
    """Enqueue one scheduled research job through the session runtime.

    ``send_message`` queues the agent attempt and returns once accepted; it
    does not wait for that agent run to reach a terminal status. The executor's
    ``COMPLETED`` state for this dispatch path means "successfully enqueued."
    """
    svc = _get_session_service()
    if not svc:
        raise RuntimeError("Session runtime not enabled")
    # Pass a copy so the session runtime's internal config writes (e.g.
    # include_shell_tools) do not mutate the persisted scheduled-run config.
    session = svc.create_session(title=f"scheduled-research:{job.id}", config=dict(job.config))
    logger.info("dispatching scheduled research job %s via session %s", job.id, session.session_id)
    await svc.send_message(session.session_id, job.prompt)


def _get_scheduled_research_executor() -> "ScheduledResearchExecutor":
    """Return the singleton scheduled research executor."""
    global _scheduled_research_executor
    if _scheduled_research_executor is None:
        from src.scheduled_research.executor import ScheduledResearchExecutor

        _scheduled_research_executor = ScheduledResearchExecutor(
            _get_scheduled_research_store(),
            _dispatch_scheduled_research_job,
            enabled=_scheduled_research_scheduler_enabled(),
        )
    return _scheduled_research_executor


def _start_scheduled_research_executor() -> None:
    """Start scheduled research execution when explicitly enabled."""
    if not _scheduled_research_scheduler_enabled():
        return
    _get_scheduled_research_executor().start()


async def _stop_scheduled_research_executor() -> None:
    """Stop scheduled research execution if it was started."""
    executor = _scheduled_research_executor
    if executor is not None:
        await executor.stop()


class CreateScheduledRunRequest(BaseModel):
    """Request body for POST /scheduled-runs."""

    id: Optional[str] = Field(None, description="Job id; auto-generated UUID when omitted")
    prompt: str = Field(..., min_length=1, description="Research prompt or backtest description")
    schedule: str = Field(..., min_length=1, description="Interval-ms or 5-field cron expression")
    next_run_at: Optional[int] = Field(None, description="Epoch-ms for next run; defaults to now")
    config: Dict[str, Any] = Field(default_factory=dict, description="Optional backtest parameters")


class ScheduledRunResponse(BaseModel):
    """API response for a single scheduled job."""

    id: str
    prompt: str
    schedule: str
    next_run_at: int
    status: str
    created_at: int
    config: Dict[str, Any] = Field(default_factory=dict)


@app.post(
    "/scheduled-runs",
    response_model=ScheduledRunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_auth)],
)
async def create_scheduled_run(request: CreateScheduledRunRequest) -> ScheduledRunResponse:
    """Create (or replace) a scheduled research job.

    The job is persisted immediately. No execution is triggered.
    """
    import time

    from src.scheduled_research.models import JobStatus, ScheduledResearchJob
    from src.scheduled_research.models import validate_schedule

    try:
        validate_schedule(request.schedule)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    now_ms = int(time.time() * 1000)
    job = ScheduledResearchJob(
        id=request.id or str(uuid.uuid4()),
        prompt=request.prompt,
        schedule=request.schedule,
        next_run_at=request.next_run_at if request.next_run_at is not None else now_ms,
        status=JobStatus.PENDING,
        created_at=now_ms,
        config=request.config,
    )
    _get_scheduled_research_store().upsert(job)
    return ScheduledRunResponse(**job.to_dict())


@app.get(
    "/scheduled-runs",
    response_model=List[ScheduledRunResponse],
    dependencies=[Depends(require_auth)],
)
async def list_scheduled_runs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
) -> List[ScheduledRunResponse]:
    """List scheduled research jobs, optionally filtered by status."""
    jobs = _get_scheduled_research_store().list_jobs(status=status_filter, limit=limit)
    return [ScheduledRunResponse(**j.to_dict()) for j in jobs]


@app.delete(
    "/scheduled-runs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_auth)],
)
async def delete_scheduled_run(job_id: str) -> None:
    """Cancel (delete) a scheduled research job by id."""
    _validate_path_param(job_id, "job_id")
    removed = _get_scheduled_research_store().delete(job_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"scheduled run {job_id} not found")


# ============================================================================
# Main Entry Point
# ============================================================================

def serve_main(argv: list[str] | None = None) -> int:
    """Start the API server from CLI-style arguments."""
    import argparse
    import subprocess
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from starlette.exceptions import HTTPException as StarletteHTTPException

    class SPAStaticFiles(StaticFiles):
        """Serve index.html for browser refreshes on client-side routes."""

        async def get_response(self, path: str, scope: Dict[str, Any]):
            try:
                return await super().get_response(path, scope)
            except StarletteHTTPException as exc:
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    raise
                return await super().get_response("index.html", scope)

    parser = argparse.ArgumentParser(description="Vibe-Trading Server")
    parser.add_argument("--port", type=int, default=8000, help="Listen port (default 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--dev", action="store_true", help="Dev mode: spawn Vite on :5173")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    frontend_root = Path(__file__).resolve().parent.parent / "frontend"

    vite_proc = None
    if args.dev and frontend_root.exists():
        print("[dev] Starting Vite dev server on :5173 ...")
        vite_proc = subprocess.Popen(
            ["npx", "vite", "--host", "0.0.0.0"],
            cwd=str(frontend_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[dev] Vite PID={vite_proc.pid}")
        print("[dev] Frontend: http://localhost:5173")
        print(f"[dev] API: http://localhost:{args.port}")
    elif frontend_dist.exists():
        if not any(route.path == "/" for route in app.routes):
            app.mount("/", SPAStaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        print(f"[prod] Frontend served from {frontend_dist}")
    else:
        print(f"[warn] No frontend build found at {frontend_dist}")
        print("[warn] Run: cd frontend && npm run build")

    print("=" * 50)
    print("  Vibe-Trading Server")
    print(f"  http://127.0.0.1:{args.port}")
    print("=" * 50)

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        if vite_proc:
            vite_proc.terminate()
            print("[dev] Vite stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(serve_main())
