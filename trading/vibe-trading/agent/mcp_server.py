#!/usr/bin/env python3
"""Vibe-Trading MCP Server — expose finance research tools to any MCP client.

Works with OpenClaw, Claude Desktop, Cursor, and any MCP-compatible client.
Zero API key required for HK/US/crypto research markets (yfinance, OKX,
AKShare are free). Trading connector tools are profile-scoped and require the
selected connector's own local app or OAuth setup.

Surfaces 54 tools: skills, research goals, backtest/factor/options/pattern
analysis, market data, fundamentals & capital-flow & news & discovery
(get_fund_flow / get_dragon_tiger / get_northbound_flow / get_margin_trading /
get_block_trades / get_shareholder_count / get_lockup_expiry / get_sector_info /
get_research_reports / get_stock_news / get_sec_filings /
get_financial_statements / get_options_chain / get_stock_profile /
screen_market / search_symbol / get_macro_series / iwencai_search), read-only
trading-connector reads, swarm orchestration, trade-journal and shadow-account
analysis. Every exposed tool is read-only or research-only; no order-placing or
order-cancelling tool is ever surfaced via MCP.

Usage:
    python mcp_server.py                    # stdio transport (default)
    python mcp_server.py --transport sse    # SSE transport for web clients

OpenClaw config (~/.openclaw/config.yaml):
    skills:
      - name: vibe-trading
        command: python /path/to/agent/mcp_server.py

Claude Desktop config:
    {
      "mcpServers": {
        "vibe-trading": {
          "command": "python",
          "args": ["/path/to/agent/mcp_server.py"]
        }
      }
    }
"""

from __future__ import annotations

# ruff: noqa: E402

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Ensure agent/ is on sys.path
AGENT_DIR = Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from fastmcp import Context, FastMCP
from cli._version import __version__ as APP_VERSION
from src.market_data import (
    DEFAULT_MAX_ROWS,
    cap_rows,
    detect_source,
    fetch_market_data_json,
    get_loader,
)

mcp = FastMCP("Vibe-Trading", version=APP_VERSION)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------

_skills_loader = None
_registry = None
_goal_store = None
_include_shell_tools = True


def _env_shell_tools_enabled() -> bool:
    """Return whether shell tools were explicitly enabled for network MCP."""
    return os.getenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", "").strip().lower() in {"1", "true", "yes", "on"}


def _get_skills_loader():
    global _skills_loader
    if _skills_loader is None:
        from src.agent.skills import SkillsLoader

        _skills_loader = SkillsLoader()
    return _skills_loader


def _get_registry():
    global _registry
    if _registry is None:
        from src.tools import build_registry

        _registry = build_registry(include_shell_tools=_include_shell_tools)
    return _registry


def _get_goal_store():
    """Return the shared finance goal store."""
    global _goal_store
    if _goal_store is None:
        from src.goal import GoalStore

        _goal_store = GoalStore()
    return _goal_store


def _json_ok(**payload: Any) -> str:
    """Return a standard MCP JSON success envelope."""
    return json.dumps({"status": "ok", **payload}, ensure_ascii=False, indent=2)


def _json_error(error: str, *, error_type: str = "error") -> str:
    """Return a standard MCP JSON error envelope."""
    return json.dumps(
        {"status": "error", "error_type": error_type, "error": error},
        ensure_ascii=False,
        indent=2,
    )


def _default_goal_criteria() -> list[str]:
    """Return the MVP finance protocol checklist."""
    from src.goal.context import default_goal_criteria

    return default_goal_criteria()


def _clean_list(value: list[str] | None) -> list[str]:
    """Strip empty list values from MCP payloads."""
    return [item.strip() for item in (value or []) if item and item.strip()]


def _blank_to_none(value: str | None) -> str | None:
    """Normalize blank MCP strings to None."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _audit_rows_from_payload(value: list[dict[str, Any]] | None):
    """Parse MCP completion audit rows."""
    from src.goal import AuditRow

    rows = []
    for item in value or []:
        criterion_id = str(item.get("criterion_id") or "").strip()
        result = str(item.get("result") or "").strip()
        if not criterion_id or not result:
            raise ValueError("audit rows require criterion_id and result")
        rows.append(
            AuditRow(
                criterion_id=criterion_id,
                result=result,
                evidence_ids=_clean_list(item.get("evidence_ids") or []),
                notes=str(item.get("notes") or ""),
            )
        )
    return rows


def _risk_tier_from_text(value: str):
    """Parse and validate goal risk tier."""
    from src.goal import RiskTier

    risk_tier = RiskTier(value)
    if risk_tier is RiskTier.LIVE_TRADING_OR_EXECUTION:
        raise ValueError("live trading or execution goals are not supported")
    return risk_tier


# ---------------------------------------------------------------------------
# Skill tools
# ---------------------------------------------------------------------------


@mcp.tool
def list_skills() -> str:
    """List all available finance skills with names and descriptions.

    Returns a JSON array of {name, description} for all loaded skills.
    Use load_skill(name) to get the full documentation for any skill.
    """
    loader = _get_skills_loader()
    skills = [{"name": s.name, "description": s.description} for s in loader.skills]
    return json.dumps(skills, ensure_ascii=False, indent=2)


@mcp.tool
def load_skill(name: str) -> str:
    """Load full documentation for a named finance skill.

    Each skill is a comprehensive knowledge document covering methodology,
    code templates, parameters, and examples. Use list_skills() first to
    discover available skills.

    Args:
        name: Skill name (e.g. 'strategy-generate', 'risk-analysis', 'technical-basic').
    """
    loader = _get_skills_loader()
    content = loader.get_content(name)
    if content.startswith("Error:"):
        return json.dumps({"status": "error", "error": content}, ensure_ascii=False)
    return json.dumps({"status": "ok", "skill": name, "content": content}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Goal tools
# ---------------------------------------------------------------------------


@mcp.tool
def start_research_goal(
    session_id: str,
    objective: str,
    criteria: list[str] | None = None,
    ui_summary: str = "",
    protocol: str = "thesis_review",
    risk_tier: str = "research_general",
    token_budget: int | None = None,
    turn_budget: int | None = None,
    time_budget_seconds: int | None = None,
) -> str:
    """Create or replace the current finance research goal for a session.

    This is the MCP entry point for long-running, research-only finance tasks.
    It creates an auditable goal with checklist criteria and supersedes any
    previous current goal for the same session.

    Args:
        session_id: External conversation/session id owned by the MCP client.
        objective: Research-only objective, not a trade execution request.
        criteria: Optional checklist. Defaults to the MVP finance protocol.
        ui_summary: Optional compact label for UI surfaces.
        protocol: Research protocol name. Defaults to thesis_review.
        risk_tier: One of the supported non-execution risk tiers.
        token_budget: Optional token budget.
        turn_budget: Optional turn budget.
        time_budget_seconds: Optional wall-clock budget.
    """
    try:
        clean_criteria = _clean_list(criteria) or _default_goal_criteria()
        goal = _get_goal_store().replace_goal(
            session_id=session_id.strip(),
            objective=objective,
            criteria=clean_criteria,
            ui_summary=ui_summary,
            source="mcp",
            protocol=protocol,
            risk_tier=_risk_tier_from_text(risk_tier),
            token_budget=token_budget,
            turn_budget=turn_budget,
            time_budget_seconds=time_budget_seconds,
        )
        snapshot = _get_goal_store().get_goal_snapshot(goal.goal_id)
        return _json_ok(snapshot=snapshot)
    except ValueError as exc:
        return _json_error(str(exc), error_type="validation")


@mcp.tool
def get_research_goal(session_id: str) -> str:
    """Return the current finance research goal snapshot for a session.

    Args:
        session_id: External conversation/session id owned by the MCP client.
    """
    try:
        snapshot = _get_goal_store().get_current_snapshot(session_id.strip())
    except ValueError as exc:
        return _json_error(str(exc), error_type="validation")
    if snapshot is None:
        return _json_error("No current goal", error_type="not_found")
    return _json_ok(snapshot=snapshot)


@mcp.tool
def add_goal_evidence(
    session_id: str,
    goal_id: str,
    expected_goal_id: str,
    text: str,
    criterion_id: str | None = None,
    claim_id: str | None = None,
    evidence_type: str = "evidence",
    tool_call_id: str | None = None,
    run_id: str | None = None,
    source_provider: str | None = None,
    source_type: str | None = None,
    source_uri: str | None = None,
    symbol_universe: list[str] | None = None,
    benchmark: list[str] | None = None,
    timeframe: str | None = None,
    method: str | None = None,
    assumptions: dict[str, Any] | None = None,
    artifact_path: str | None = None,
    artifact_hash: str | None = None,
    data_as_of: str | None = None,
    confidence: str | None = None,
    caveat: str | None = None,
    contradicts_claim_ids: list[str] | None = None,
) -> str:
    """Append traceable evidence to a finance research goal.

    Args:
        session_id: External conversation/session id.
        goal_id: Goal being mutated.
        expected_goal_id: Goal id captured before the tool/model turn started.
        text: Evidence note or result summary.
        criterion_id: Optional criterion this evidence satisfies.
        claim_id: Optional claim this evidence supports or contradicts.
        evidence_type: Evidence category, default evidence.
        tool_call_id: Source tool call id for traceability; it does not verify evidence by itself.
        run_id: Vibe-Trading run id. It verifies evidence only when the run directory exists.
        source_provider: Data/provider name such as yfinance, OKX, tushare.
        source_type: Source category such as market_data, document, backtest.
        source_uri: Optional source URL/path.
        symbol_universe: Symbols covered by the evidence.
        benchmark: Benchmark symbols covered by the evidence.
        timeframe: Market timeframe.
        method: Research method used.
        assumptions: Structured assumptions.
        artifact_path: Artifact path. It verifies evidence only when allowed by path policy and paired with a matching sha256 hash.
        artifact_hash: Required sha256 when artifact_path should verify evidence.
        data_as_of: ISO timestamp/date for data freshness.
        confidence: Optional confidence label.
        caveat: Optional limitation note.
        contradicts_claim_ids: Claim ids contradicted by this evidence.
    """
    try:
        from src.goal import EvidenceInput, StaleGoalError

        evidence = _get_goal_store().append_evidence(
            session_id=session_id.strip(),
            goal_id=goal_id.strip(),
            expected_goal_id=expected_goal_id.strip(),
            evidence=EvidenceInput(
                criterion_id=_blank_to_none(criterion_id),
                claim_id=_blank_to_none(claim_id),
                evidence_type=evidence_type,
                text=text,
                tool_call_id=_blank_to_none(tool_call_id),
                run_id=_blank_to_none(run_id),
                source_provider=_blank_to_none(source_provider),
                source_type=_blank_to_none(source_type),
                source_uri=_blank_to_none(source_uri),
                symbol_universe=_clean_list(symbol_universe),
                benchmark=_clean_list(benchmark),
                timeframe=_blank_to_none(timeframe),
                method=_blank_to_none(method),
                assumptions=assumptions or {},
                artifact_path=_blank_to_none(artifact_path),
                artifact_hash=_blank_to_none(artifact_hash),
                data_as_of=_blank_to_none(data_as_of),
                confidence=_blank_to_none(confidence),
                caveat=_blank_to_none(caveat),
                contradicts_claim_ids=_clean_list(contradicts_claim_ids),
            ),
        )
        snapshot = _get_goal_store().get_goal_snapshot(goal_id.strip())
        if snapshot is None:
            return _json_error("Goal snapshot could not be reloaded")
        from dataclasses import asdict

        return _json_ok(evidence=asdict(evidence), snapshot=snapshot)
    except StaleGoalError as exc:
        return _json_error(str(exc), error_type="stale_goal")
    except ValueError as exc:
        return _json_error(str(exc), error_type="validation")


@mcp.tool
def update_research_goal_status(
    session_id: str,
    goal_id: str,
    expected_goal_id: str,
    status: str,
    audit: list[dict[str, Any]] | None = None,
    recap: str | None = None,
) -> str:
    """Update a finance research goal status after an audit.

    Use this to complete, cancel, block, pause, or otherwise move the current
    goal through its lifecycle. ``complete`` requires one audit row per
    required criterion and verified evidence for satisfied rows.

    Args:
        session_id: External conversation/session id.
        goal_id: Goal being mutated.
        expected_goal_id: Goal id captured before the tool/model turn started.
        status: Goal lifecycle status, e.g. complete, cancelled, blocked.
        audit: Optional list of criterion audit rows.
        recap: Optional concise status recap.
    """
    try:
        from src.goal import GoalStatus, StaleGoalError

        updated = _get_goal_store().update_status(
            session_id=session_id.strip(),
            goal_id=goal_id.strip(),
            expected_goal_id=expected_goal_id.strip(),
            status=GoalStatus(status),
            audit=_audit_rows_from_payload(audit),
            recap=_blank_to_none(recap),
        )
        snapshot = _get_goal_store().get_goal_snapshot(updated.goal_id)
        if snapshot is None:
            return _json_error("Goal snapshot could not be reloaded")
        return _json_ok(goal=snapshot["goal"], snapshot=snapshot)
    except StaleGoalError as exc:
        return _json_error(str(exc), error_type="stale_goal")
    except ValueError as exc:
        return _json_error(str(exc), error_type="validation")


# ---------------------------------------------------------------------------
# Backtest tool
# ---------------------------------------------------------------------------


@mcp.tool
def backtest(run_dir: str) -> str:
    """Run a vectorized backtest using config.json and code/signal_engine.py.

    The run_dir must contain:
    - config.json: backtest configuration (source, codes, dates, etc.)
    - code/signal_engine.py: strategy signal generation code

    Supported data sources (set in config.json "source" field):
    - "yfinance": HK/US equities (free, no API key needed)
    - "okx": cryptocurrency (free, no API key needed)
    - "tushare": China A-shares (requires TUSHARE_TOKEN env var)
    - "akshare": A-shares, US, HK, futures, forex (free, no API key)
    - "ccxt": crypto from 100+ exchanges (free, no API key)
    - "auto": auto-detect based on symbol format (with fallback)

    Returns metrics (Sharpe, return, drawdown, etc.) and artifact paths.

    Args:
        run_dir: Path to the run directory containing config.json and code/.
    """
    from src.tools.backtest_tool import run_backtest

    return run_backtest(run_dir)


# ---------------------------------------------------------------------------
# Factor analysis tool
# ---------------------------------------------------------------------------


@mcp.tool
def factor_analysis(
    codes: list[str],
    factor_name: str,
    start_date: str,
    end_date: str,
    source: str = "auto",
    top_n: int = 10,
    bottom_n: int = 10,
) -> str:
    """Compute factor IC/IR analysis and layered backtest for a cross-section of stocks.

    Analyzes factor predictive power using Spearman rank IC, IR (IC/std),
    and top/bottom quintile return spreads.

    Args:
        codes: List of stock codes (e.g. ["000001.SZ", "600519.SH"]).
        factor_name: Factor column name in daily_basic data (e.g. "pe_ttm", "pb", "turnover_rate").
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        source: Data source ("tushare", "yfinance", "auto").
        top_n: Number of top-ranked stocks per period.
        bottom_n: Number of bottom-ranked stocks per period.
    """
    registry = _get_registry()
    return registry.execute(
        "factor_analysis",
        {
            "codes": codes,
            "factor_name": factor_name,
            "start_date": start_date,
            "end_date": end_date,
            "source": source,
            "top_n": top_n,
            "bottom_n": bottom_n,
        },
    )


# ---------------------------------------------------------------------------
# Options pricing tool
# ---------------------------------------------------------------------------


@mcp.tool
def analyze_options(
    spot: float,
    strike: float,
    expiry_days: int,
    risk_free_rate: float = 0.03,
    volatility: float = 0.25,
    option_type: str = "call",
) -> str:
    """Calculate Black-Scholes option price and Greeks (Delta, Gamma, Theta, Vega).

    Args:
        spot: Current underlying price.
        strike: Strike price.
        expiry_days: Days until expiration.
        risk_free_rate: Annual risk-free rate (default 0.03 = 3%).
        volatility: Annual volatility (default 0.25 = 25%).
        option_type: "call" or "put".
    """
    registry = _get_registry()
    return registry.execute(
        "options_pricing",
        {
            "spot": spot,
            "strike": strike,
            "expiry_days": expiry_days,
            "risk_free_rate": risk_free_rate,
            "volatility": volatility,
            "option_type": option_type,
        },
    )


# ---------------------------------------------------------------------------
# Pattern recognition tool
# ---------------------------------------------------------------------------


@mcp.tool
def pattern_recognition(run_dir: str) -> str:
    """Detect technical chart patterns (head-and-shoulders, double top/bottom,
    triangles, wedges, channels) in OHLCV data.

    Reads price data from run_dir/artifacts/ohlcv_*.csv files.
    Can be called before coding (to inform strategy) or after backtest (to analyse).

    Args:
        run_dir: Path to run directory containing artifacts/ohlcv_*.csv.
    """
    registry = _get_registry()
    return registry.execute("pattern", {"run_dir": run_dir})


# ---------------------------------------------------------------------------
# Web & document reading tools
# ---------------------------------------------------------------------------


@mcp.tool
def read_url(url: str) -> str:
    """Fetch a web page and convert it to clean Markdown text.

    Strips ads, navigation, and styling. Useful for reading API docs,
    financial articles, research reports, and GitHub READMEs.

    Args:
        url: Target URL to read.
    """
    from src.tools.web_reader_tool import read_url as _read_url

    return _read_url(url)


@mcp.tool
def read_document(file_path: str) -> str:
    """Extract text from a PDF document with OCR fallback for scanned pages.

    Supports text-based and image-based PDFs. Automatically uses OCR
    for pages with insufficient extractable text.

    Args:
        file_path: Absolute path to the PDF file.
    """
    registry = _get_registry()
    return registry.execute("read_document", {"file_path": file_path})


# ---------------------------------------------------------------------------
# Web search tool
# ---------------------------------------------------------------------------


@mcp.tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo and return top results.

    Returns titles, URLs, and snippets. Use read_url() to fetch full content
    from any result URL. Free, no API key required.

    Args:
        query: Search query string.
        max_results: Maximum results to return (default 5, max 10).
    """
    registry = _get_registry()
    return registry.execute(
        "web_search",
        {
            "query": query,
            "max_results": min(max_results, 10),
        },
    )


# ---------------------------------------------------------------------------
# File I/O tools (sandboxed to workspace)
# ---------------------------------------------------------------------------


@mcp.tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Used to create config.json and signal_engine.py
    for backtesting workflows.

    Args:
        path: File path (relative to workspace or absolute).
        content: File content to write.
    """
    registry = _get_registry()
    return registry.execute("write_file", {"path": path, "content": content})


@mcp.tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: File path to read.
    """
    registry = _get_registry()
    return registry.execute("read_file", {"path": path})


# ---------------------------------------------------------------------------
# Trading connector tools
# ---------------------------------------------------------------------------


def _trading_common_args(
    *,
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    """Build shared optional trading connector arguments."""
    payload: dict[str, Any] = {}
    if connection:
        payload["connection"] = connection
    if host:
        payload["host"] = host
    if port is not None:
        payload["port"] = port
    if client_id is not None:
        payload["client_id"] = client_id
    if account:
        payload["account"] = account
    return payload


@mcp.tool
def trading_connections() -> str:
    """List selectable trading connector profiles.

    The connector is the first-level choice. Paper/live is an attribute of each
    profile under that connector.
    """
    registry = _get_registry()
    return registry.execute("trading_connections", {})


@mcp.tool
def trading_select_connection(connection: str) -> str:
    """Select the default trading connector profile for later trading_* calls.

    Args:
        connection: Profile id, e.g. ``ibkr-paper-local`` or ``robinhood-live-mcp``.
    """
    registry = _get_registry()
    return registry.execute("trading_select_connection", {"connection": connection})


@mcp.tool
def trading_check(
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> str:
    """Check whether a trading connector profile is configured and reachable.

    This never places orders. For local profiles, it checks the user's local
    app/socket. For remote MCP profiles, it reports config and OAuth-token
    presence without returning secrets.

    Args:
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
    """
    registry = _get_registry()
    return registry.execute(
        "trading_check",
        _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account),
    )


@mcp.tool
def trading_account(
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> str:
    """Read account data from the selected trading connector profile.

    Args:
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
    """
    registry = _get_registry()
    return registry.execute(
        "trading_account",
        _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account),
    )


@mcp.tool
def trading_positions(
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> str:
    """Read positions from the selected trading connector profile.

    Args:
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
    """
    registry = _get_registry()
    return registry.execute(
        "trading_positions",
        _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account),
    )


@mcp.tool
def trading_orders(
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    include_executions: bool = False,
) -> str:
    """Read open orders from the selected trading connector profile.

    Read-only: this tool does not place, cancel, modify, or replace orders.

    Args:
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
        include_executions: Include recent executions when available.
    """
    params = _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account)
    params["include_executions"] = include_executions
    registry = _get_registry()
    return registry.execute("trading_orders", params)


@mcp.tool
def trading_quote(
    symbol: str,
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
) -> str:
    """Read a quote snapshot from the selected trading connector profile.

    Args:
        symbol: Symbol such as AAPL.
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
        exchange: Exchange routing, default SMART.
        currency: Contract currency, default USD.
        sec_type: Security type, default STK.
    """
    params = _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account)
    params.update({"symbol": symbol, "exchange": exchange, "currency": currency, "sec_type": sec_type})
    registry = _get_registry()
    return registry.execute("trading_quote", params)


@mcp.tool
def trading_history(
    symbol: str,
    connection: str | None = None,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
    duration: str = "30 D",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
) -> str:
    """Read historical bars from the selected trading connector profile.

    Args:
        symbol: Symbol such as AAPL.
        connection: Optional profile id. Defaults to the selected profile.
        host: Optional local host override.
        port: Optional local socket port override.
        client_id: Optional local client id override.
        account: Optional account code filter.
        exchange: Exchange routing, default SMART.
        currency: Contract currency, default USD.
        sec_type: Security type, default STK.
        duration: IBKR duration string, default 30 D.
        bar_size: IBKR bar size, default 1 day.
        what_to_show: Data type, default TRADES.
        use_rth: Use regular trading hours.
    """
    params = _trading_common_args(connection=connection, host=host, port=port, client_id=client_id, account=account)
    params.update(
        {
            "symbol": symbol,
            "exchange": exchange,
            "currency": currency,
            "sec_type": sec_type,
            "duration": duration,
            "bar_size": bar_size,
            "what_to_show": what_to_show,
            "use_rth": use_rth,
        }
    )
    registry = _get_registry()
    return registry.execute("trading_history", params)


# ---------------------------------------------------------------------------
# Swarm team tool
# ---------------------------------------------------------------------------


@mcp.tool
def list_swarm_presets() -> str:
    """List available swarm multi-agent team presets.

    Each preset defines a team of specialized agents (e.g. investment committee,
    quant desk, risk committee) that collaborate on complex research tasks.
    Returns preset names, descriptions, agent counts, and required variables.
    """
    from src.swarm.presets import list_presets

    presets = list_presets()
    return json.dumps(presets, ensure_ascii=False, indent=2)


@mcp.tool
async def run_swarm(
    preset_name: str,
    variables: dict[str, str],
    wait_seconds: int = 3600,
    start_only: bool = False,
    ctx: Context | None = None,
) -> str:
    """Run a swarm multi-agent team and stream progress back to the caller.

    Assembles a team of specialized agents that collaborate through a DAG workflow.
    For example, the 'investment_committee' preset runs bull analyst, bear analyst,
    risk officer, and portfolio manager in sequence.

    Use list_swarm_presets() to see available presets and their required variables.

    The tool keeps the MCP call open via ``Context.report_progress`` while the
    swarm runs, so the caller sees live "N/M tasks complete" updates instead
    of timing out silently. Only if ``wait_seconds`` is exhausted does the
    tool return early with the current ``run_id`` — call ``get_run_result``
    afterwards to fetch the final report.

    Args:
        preset_name: Swarm preset name (e.g. 'investment_committee', 'quant_strategy_desk').
        variables: Required variables for the preset (e.g. {"target": "AAPL.US", "market": "US"}).
        wait_seconds: Maximum seconds to keep the MCP call open. Default 3600
            (1 hour); the progress-notification keepalive means the transport
            stays connected for the full budget.
        start_only: If True, kick off the run and return immediately with
            ``run_id`` + current status. Ignores ``wait_seconds``.
    """
    import asyncio
    import time
    from src.config import load_swarm_agent_config
    from src.swarm.runtime import SwarmRuntime
    from src.swarm.store import SwarmStore, swarm_runs_root

    swarm_dir = swarm_runs_root()
    store = SwarmStore(base_dir=swarm_dir)
    # Boot-time / operator-trusted: resolved from env var or on-disk config.
    # The MCP caller (this tool's invoker) cannot influence the path — the
    # ``variables`` arg below is template data, never config (R-06).
    agent_config = load_swarm_agent_config()
    runtime = SwarmRuntime(store=store, agent_config=agent_config)

    try:
        run = runtime.start_run(
            preset_name, variables, include_shell_tools=_include_shell_tools
        )
    except FileNotFoundError as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
    except ValueError as exc:
        return json.dumps({"status": "error", "error": f"DAG validation failed: {exc}"}, ensure_ascii=False)

    if start_only or wait_seconds <= 0:
        return json.dumps(
            _build_run_payload(store, run.id, preset_name, timed_out=False),
            ensure_ascii=False,
            indent=2,
        )

    # Surface the run_id immediately in a fixed-format progress message so a
    # caller whose transport drops mid-run (or whose MCP client enforces a
    # hard tool-call timeout that ignores progress notifications) can still
    # recover the run via ``get_run_result(run_id)``. Parsers should match
    # ``swarm_started run_id=<id>`` literally; later frames are free-form.
    if ctx is not None:
        try:
            await ctx.report_progress(
                progress=0,
                total=1,
                message=f"swarm_started run_id={run.id} preset={preset_name}",
            )
        except Exception:
            pass

    terminal = {"completed", "failed", "cancelled"}
    started_at = time.monotonic()
    deadline = started_at + wait_seconds
    while True:
        payload = _build_run_payload(store, run.id, preset_name, timed_out=False)
        if payload["status"] == "error":
            return json.dumps(payload, ensure_ascii=False)
        if payload["status"] in terminal:
            return json.dumps(payload, ensure_ascii=False, indent=2)

        # Emit a progress frame every loop, NOT only on state change — MCP
        # clients use these as transport keepalive. A long task that doesn't
        # transition for 30 minutes still needs ticks or the client times out.
        # ``elapsed`` keeps the message content fresh so dedup-on-message
        # clients still see updates.
        if ctx is not None:
            tasks = payload.get("tasks") or []
            total = max(1, len(tasks))
            done = sum(1 for t in tasks if t.get("status") in terminal)
            elapsed = int(time.monotonic() - started_at)
            try:
                await ctx.report_progress(
                    progress=done,
                    total=total,
                    message=f"{done}/{total} tasks complete · {elapsed}s elapsed (run {run.id})",
                )
            except Exception:
                pass

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            payload = _build_run_payload(store, run.id, preset_name, timed_out=True)
            return json.dumps(payload, ensure_ascii=False, indent=2)
        await asyncio.sleep(min(5.0, remaining))


# ---------------------------------------------------------------------------
# Market data tool
# ---------------------------------------------------------------------------

def _detect_source(code: str) -> str:
    return detect_source(code)


def _get_loader(source: str):
    """Get loader class via registry with fallback support."""
    return get_loader(source)


def _cap_rows(records: list, max_rows: int) -> list | dict[str, object]:
    """Bound a per-symbol row list to keep the MCP payload within budget.

    max_rows==0 disables the cap (full list, unchanged shape). A negative
    max_rows is invalid and enforces the default cap (never unbounded).
    Otherwise an oversized symbol is *evenly strided* — every step-th bar,
    with the last bar pinned — so the returned series spans the full range
    (no head+tail gap, no synthetic ``_gap`` sentinel). Symbols within the
    cap are returned unchanged (plain list) — small queries are
    byte-identical.
    """
    return cap_rows(records, max_rows)


@mcp.tool
def get_market_data(
    codes: list[str],
    start_date: str,
    end_date: str,
    source: str = "auto",
    interval: str = "1D",
    max_rows: int = DEFAULT_MAX_ROWS,
) -> str:
    """Fetch OHLCV market data for stocks, crypto, or mixed symbols.

    Supported sources:
    - "yfinance": HK/US equities (free, e.g. AAPL.US, 700.HK)
    - "okx": cryptocurrency (free, e.g. BTC-USDT, ETH-USDT)
    - "tushare": China A-shares (requires TUSHARE_TOKEN, e.g. 000001.SZ)
    - "baostock": China A-shares via TCP protocol, bypasses HTTP CDN blocks (e.g. 000001.SZ, 601595.SH)
    - "tencent": China A-shares via Tencent Finance API (e.g. 000001.SZ, 601595.SH)
    - "akshare": A-shares, US, HK, futures, forex (free, e.g. 000001.SZ, AAPL.US)
    - "ccxt": crypto from 100+ exchanges (free, e.g. BTC/USDT)
    - "auto": auto-detect based on symbol format (with fallback)

    Args:
        codes: List of symbols (e.g. ["AAPL.US", "BTC-USDT", "000001.SZ"]).
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        source: Data source ("auto", "yfinance", "okx", "tushare", "baostock", "tencent", "akshare", "ccxt").
        interval: Bar size (1m/5m/15m/30m/1H/4H/1D, default "1D").
        max_rows: Per-symbol row cap (default 250) so the response stays
            within the MCP token budget. A symbol exceeding it returns an
            even-stride downsample (every step-th bar, last bar pinned)
            plus truncation metadata. Set max_rows=0 for all rows
            (unbounded, legacy behavior).
    """
    return fetch_market_data_json(
        codes=codes,
        start_date=start_date,
        end_date=end_date,
        source=source,
        interval=interval,
        max_rows=max_rows,
        loader_resolver=_get_loader,
    )


# ---------------------------------------------------------------------------
# Read-only fundamentals, flow, news & discovery tools
#
# Each wrapper delegates to the auto-discovered local registry, exactly like
# factor_analysis / pattern_recognition above. The registry returns a clean
# JSON error envelope when a key-gated tool (get_macro_series needs
# FRED_API_KEY, iwencai_search needs VIBE_TRADING_IWENCAI_KEY) is absent — see
# ``_execute_key_gated`` below, which honours that contract even though the
# tool is excluded from the registry by ``check_available()``. Every tool below
# is strictly read-only data — no order/trading tool is ever surfaced via MCP.
# ---------------------------------------------------------------------------


# Map of key-gated MCP tools to their concrete tool class. When the required
# API key is unset the class' ``check_available()`` returns False, so the tool
# is excluded from the auto-discovered registry and ``registry.execute`` would
# answer with a generic "Tool not found". That contradicts the documented
# contract above (a clean, env-var-named error). For these tools we therefore
# fall through to the tool's own ``execute()`` — whose missing-key envelope
# names the exact env var (``FRED_API_KEY`` / ``VIBE_TRADING_IWENCAI_KEY``).
def _key_gated_tool_classes() -> dict[str, Any]:
    """Return the {tool_name: tool_class} map for key-gated MCP tools.

    Imported lazily so a missing optional dependency in either module degrades
    to the registry path rather than breaking module import.

    Returns:
        Mapping of MCP tool name to its ``BaseTool`` subclass.
    """
    from src.tools.fred_macro_tool import FredMacroTool
    from src.tools.iwencai_tool import IWenCaiSearchTool

    return {
        "get_macro_series": FredMacroTool,
        "iwencai_search": IWenCaiSearchTool,
    }


def _execute_key_gated(name: str, params: dict[str, Any]) -> str:
    """Run a key-gated read-only tool, preserving its env-var-named error.

    Prefers the auto-discovered registry (present when the API key is set). When
    the key is absent the tool is excluded from the registry, so we invoke its
    concrete ``execute()`` directly to surface the documented missing-key error
    that names the exact env var — never a generic "Tool not found".

    Args:
        name: MCP tool name (``get_macro_series`` or ``iwencai_search``).
        params: Keyword arguments forwarded to the tool.

    Returns:
        The tool's JSON envelope as a string.
    """
    registry = _get_registry()
    if registry.get(name) is not None:
        return registry.execute(name, params)
    tool_cls = _key_gated_tool_classes().get(name)
    if tool_cls is None:
        return registry.execute(name, params)
    return tool_cls().execute(**params)


@mcp.tool
def get_fund_flow(codes: list[str], period: str = "daily", days: int = 30) -> str:
    """Fetch order-bucket net capital inflow (main/super-large/large/medium/small).

    Markets: A-share (.SH/.SZ/.BJ), Hong Kong (.HK) and US (.US). Use this to
    gauge whether large/main-force money is flowing in or out, as daily history
    or the current session's per-minute line. One unresolvable symbol is
    reported per-symbol and does not abort the batch.

    Args:
        codes: Symbols with market suffix, e.g. ["600519.SH", "00700.HK"].
        period: "daily" (daily net-inflow history) or "min" (per-minute line).
        days: For period="daily", number of most-recent daily bars to keep.
    """
    registry = _get_registry()
    return registry.execute("get_fund_flow", {"codes": codes, "period": period, "days": days})


@mcp.tool
def get_dragon_tiger(date: str, code: str | None = None) -> str:
    """Fetch the A-share dragon-tiger board (龙虎榜) for a trade date (Eastmoney).

    Markets: China A-share (SH/SZ). Omit ``code`` for the full-market list of
    every security on the board that day; supply ``code`` to also get that
    security's ranked top buy/sell brokerage seats. Read-only, no auth.

    Args:
        date: Trade date in YYYY-MM-DD format (e.g. 2024-01-02).
        code: Optional A-share symbol or bare code (e.g. "600519.SH" or "600519").
    """
    params: dict[str, Any] = {"date": date}
    if code:
        params["code"] = code
    registry = _get_registry()
    return registry.execute("get_dragon_tiger", params)


@mcp.tool
def get_northbound_flow(lookback_days: int = 30) -> str:
    """Fetch Northbound (Stock-Connect) net capital flow for China A-shares.

    Returns the latest realtime net inflow plus recent daily history, split into
    Shanghai-Connect (沪股通) and Shenzhen-Connect (深股通) channels (units: 10k
    CNY) from Eastmoney. Read-only; China A-share market only.

    Args:
        lookback_days: Trailing trading days of daily net-inflow history to return.
    """
    registry = _get_registry()
    return registry.execute("get_northbound_flow", {"lookback_days": lookback_days})


@mcp.tool
def get_margin_trading(code: str, days: int = 30) -> str:
    """Fetch an A-share stock's daily margin-trading (融资融券) balances (Eastmoney).

    Returns outstanding financing balance, financing buy amount,
    securities-lending balance, and combined RZRQ balance, one row per trading
    day (most recent first). Read-only, no credentials, A-shares only (SH/SZ).

    Args:
        code: A-share code: bare ("600519"), suffixed ("600519.SH"), or
            exchange-prefixed ("sh600519").
        days: Number of most-recent trading days to return.
    """
    registry = _get_registry()
    return registry.execute("get_margin_trading", {"code": code, "days": days})


@mcp.tool
def get_block_trades(code: str, days: int = 30) -> str:
    """Fetch recent A-share block trades (大宗交易) for one symbol (Eastmoney).

    Returns per-deal price, volume, amount, the premium/discount versus that
    day's close, and the buyer/seller broker seats (营业部). Markets: China
    A-share only (.SH/.SZ/.BJ). Read-only.

    Args:
        code: A-share symbol with exchange suffix, e.g. "600519.SH", "830799.BJ".
        days: Lookback window in calendar days ending today.
    """
    registry = _get_registry()
    return registry.execute("get_block_trades", {"code": code, "days": days})


@mcp.tool
def get_shareholder_count(code: str, max_periods: int = 24) -> str:
    """Fetch mainland A-share quarterly shareholder count (股东户数) (Eastmoney).

    Returns holder count per report period, quarter-over-quarter change
    (absolute and percent), and average holding (shares and market value) per
    account. Markets: China A-shares only (.SH/.SZ/.BJ).

    Args:
        code: A-share symbol in <code>.<exchange> form (SH/SZ/BJ).
        max_periods: Maximum number of most-recent report periods to return.
    """
    registry = _get_registry()
    return registry.execute("get_shareholder_count", {"code": code, "max_periods": max_periods})


@mcp.tool
def get_lockup_expiry(code: str | None = None, horizon_days: int = 90) -> str:
    """Fetch Chinese A-share lockup-expiry (restricted-share unlock, 限售解禁) data.

    Pass an A-share ``code`` to get that stock's full historical unlock
    schedule, or omit it for a market-wide calendar of upcoming unlocks within
    the next ``horizon_days`` (Eastmoney). A large near-term unlock adds
    tradable supply and often pressures the stock. Read-only.

    Args:
        code: A-share symbol (e.g. "600519", "600519.SH"). Omit for a
            market-wide upcoming-unlock calendar.
        horizon_days: Upcoming-unlock window in days for the market-wide
            calendar; ignored when ``code`` is given (full history is returned).
    """
    params: dict[str, Any] = {"horizon_days": horizon_days}
    if code:
        params["code"] = code
    registry = _get_registry()
    return registry.execute("get_lockup_expiry", params)


@mcp.tool
def get_sector_info(code: str | None = None, mode: str = "membership", limit: int = 30) -> str:
    """Look up Chinese A-share sector / concept board info (Eastmoney, no auth).

    Two modes: (1) membership — given a stock ``code``, list the industry and
    concept boards it belongs to; (2) ranking — set ``mode="ranking"`` to rank
    industry boards by today's percent change (with up/down constituent counts
    and the leading stock). Market: A-share stocks.

    Args:
        code: A-share stock symbol with market suffix. Required when
            mode="membership"; ignored when mode="ranking".
        mode: "membership" (default) or "ranking".
        limit: For mode="ranking", number of top boards to return.
    """
    params: dict[str, Any] = {"mode": mode, "limit": limit}
    if code:
        params["code"] = code
    registry = _get_registry()
    return registry.execute("get_sector_info", params)


@mcp.tool
def get_research_reports(code: str, limit: int = 20) -> str:
    """Fetch mainland A-share sell-side research coverage and consensus forecasts.

    Returns recent broker research reports (title, brokerage, analyst, publish
    date, rating) with each broker's per-year EPS and PE forecasts from
    Eastmoney, plus the market consensus (mean) EPS forecast per forward fiscal
    year from THS (同花顺). Markets: China A-shares only (.SH/.SZ/.BJ).

    Args:
        code: A-share symbol in <code>.<exchange> form (SH/SZ/BJ).
        limit: Maximum number of most-recent research reports to return.
    """
    registry = _get_registry()
    return registry.execute("get_research_reports", {"code": code, "limit": limit})


@mcp.tool
def get_stock_news(code: str | None = None, scope: str = "stock", limit: int = 20) -> str:
    """Fetch recent financial news headlines, read-only and no auth.

    Markets: China A-share (SH/SZ/BJ) headlines from Eastmoney; US (.US) and
    Hong Kong (.HK) related-instrument matches from Yahoo Finance. Use scope
    "stock" with a ``code`` for one security's headlines, or scope "global"
    (no code) for broad China-market finance news.

    Args:
        code: Symbol whose news to fetch (e.g. "600519.SH", "AAPL.US").
            Required when scope="stock"; ignored when scope="global".
        scope: "stock" (default) or "global".
        limit: Maximum number of headlines to return.
    """
    params: dict[str, Any] = {"scope": scope, "limit": limit}
    if code:
        params["code"] = code
    registry = _get_registry()
    return registry.execute("get_stock_news", params)


@mcp.tool
def get_sec_filings(
    ticker: str,
    form: str | None = None,
    metric: str | None = None,
    limit: int = 20,
) -> str:
    """Fetch U.S. SEC EDGAR filings or reported XBRL financials for a company.

    Returns a list of recent filings (10-K / 10-Q / 8-K, etc.) with accession
    number, filing and report dates, and the primary-document URL; or, when
    ``metric`` is given, the reported XBRL us-gaap financial series for that
    concept (e.g. Revenues, NetIncomeLoss, Assets). Markets: United States only.

    Args:
        ticker: U.S. equity ticker, case-insensitive (e.g. "AAPL").
        form: Optional SEC form type filter (e.g. "10-K", "10-Q", "8-K").
        metric: Optional XBRL us-gaap concept name (e.g. "Revenues").
        limit: Maximum number of most-recent filings and metric points to return.
    """
    params: dict[str, Any] = {"ticker": ticker, "limit": limit}
    if form:
        params["form"] = form
    if metric:
        params["metric"] = metric
    registry = _get_registry()
    return registry.execute("get_sec_filings", params)


@mcp.tool
def get_financial_statements(code: str, statement: str = "indicators", period: str = "annual") -> str:
    """Fetch a stock's financial statements or key per-period indicators.

    Markets: A-share (.SH/.SZ/.BJ, via Sina), US (.US) and Hong Kong (.HK, via
    Eastmoney). Reports come back newest-first as flat per-period rows. Use this
    to read fundamentals before building a valuation or screen.

    Args:
        code: Single symbol with a market suffix (e.g. "600519.SH", "AAPL.US").
        statement: "balance", "income", "cashflow", or "indicators".
        period: "annual" or "quarter".
    """
    registry = _get_registry()
    return registry.execute(
        "get_financial_statements",
        {"code": code, "statement": statement, "period": period},
    )


@mcp.tool
def get_options_chain(ticker: str, expiration: int | None = None) -> str:
    """Fetch the US-listed options chain (calls and puts) for one expiration.

    Returns per-contract strike, bid/ask, last price, volume, open interest,
    implied volatility, and in-the-money flag, plus the list of available
    expirations (epoch seconds) via Yahoo Finance. Read-only US options data.

    Args:
        ticker: US underlying symbol (e.g. "AAPL" or "AAPL.US").
        expiration: Optional expiration as Unix epoch seconds (one of the
            returned expirations). Omit for the nearest expiration.
    """
    params: dict[str, Any] = {"ticker": ticker}
    if expiration is not None:
        params["expiration"] = expiration
    registry = _get_registry()
    return registry.execute("get_options_chain", params)


@mcp.tool
def get_stock_profile(ticker: str, sections: list[str] | None = None) -> str:
    """Fetch a read-only company profile for a US or HK listing (Yahoo Finance).

    Returns valuation key statistics, analyst price targets and
    earnings/revenue estimates, institutional and insider ownership, and the
    analyst recommendation trend. Use this for fundamentals and consensus
    context, not for OHLCV price bars (use get_market_data).

    Args:
        ticker: US (bare or .US suffix) or HK (zero-padded .HK code) symbol.
        sections: Profile sections to return, any of: key_stats, financials,
            earnings_trend, institution_ownership, insider_holders,
            recommendation_trend. Defaults to all sections.
    """
    params: dict[str, Any] = {"ticker": ticker}
    clean_sections = _clean_list(sections)
    if clean_sections:
        params["sections"] = clean_sections
    registry = _get_registry()
    return registry.execute("get_stock_profile", params)


@mcp.tool
def screen_market(market: str, sort_by: str = "change_pct", top_n: int = 30) -> str:
    """Screen a market's listed instruments and rank the top names by a metric.

    Use this to find today's biggest movers or most-actively-traded names
    without fetching every symbol. Markets: A-share ("a"), US ("us"), Hong
    Kong ("hk").

    Args:
        market: Market universe: "a", "us", or "hk".
        sort_by: Ranking metric (descending): "change_pct", "volume",
            "amount", or "turnover".
        top_n: Number of top-ranked instruments to return.
    """
    registry = _get_registry()
    return registry.execute("screen_market", {"market": market, "sort_by": sort_by, "top_n": top_n})


@mcp.tool
def search_symbol(query: str, limit: int = 10) -> str:
    """Resolve a company name or ticker fragment to candidate trading symbols.

    Returns candidates with their market in the project's symbol convention
    (A-shares 600519.SH, Hong Kong 00700.HK, U.S. AAPL.US, plus crypto/index/FX
    from Yahoo). Searches Eastmoney and Yahoo and, for U.S. equities, attaches
    the SEC CIK. Use this to turn an ambiguous name into a concrete symbol
    before calling get_market_data or get_sec_filings.

    Args:
        query: Free-text company name or ticker fragment (Chinese or English).
        limit: Maximum number of merged candidates to return.
    """
    registry = _get_registry()
    return registry.execute("search_symbol", {"query": query, "limit": limit})


@mcp.tool
def get_macro_series(
    series_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 2000,
) -> str:
    """Fetch a FRED macroeconomic time series from the St. Louis Fed.

    Returns dated observations of indicators such as CPI (CPIAUCSL),
    unemployment (UNRATE), real GDP (GDPC1), the federal funds rate (FEDFUNDS),
    or the 10-year Treasury yield (DGS10). Markets: US / global macro data.
    Requires a free FRED API key (FRED_API_KEY); without it the tool returns a
    not-available error.

    Args:
        series_id: FRED series identifier (e.g. "CPIAUCSL", "UNRATE").
        start_date: Inclusive window start, YYYY-MM-DD. Omit for full history.
        end_date: Inclusive window end, YYYY-MM-DD. Omit for the latest date.
        limit: Maximum number of most-recent observations to return.
    """
    params: dict[str, Any] = {"series_id": series_id, "limit": limit}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _execute_key_gated("get_macro_series", params)


@mcp.tool
def iwencai_search(query: str, limit: int = 20) -> str:
    """Run a natural-language A-share research query against iWenCai (问财).

    iWenCai is a Chinese-market semantic stock screener. Phrase the question in
    plain language (Chinese works best) and get back the matching China A-share
    (SH/SZ) securities with the metric columns iWenCai parsed from the question.
    Read-only; requires the VIBE_TRADING_IWENCAI_KEY access key (without it the
    tool returns a not-available error).

    Args:
        query: Natural-language research question (Chinese phrasing yields the
            best parse, e.g. "市盈率低于15的银行股").
        limit: Maximum securities to return.
    """
    return _execute_key_gated("iwencai_search", {"query": query, "limit": limit})


# ---------------------------------------------------------------------------
# Swarm status & history tools
# ---------------------------------------------------------------------------


def _get_swarm_store():
    from src.swarm.store import SwarmStore, swarm_runs_root

    swarm_dir = swarm_runs_root()
    swarm_dir.mkdir(parents=True, exist_ok=True)
    return SwarmStore(base_dir=swarm_dir)


def _run_to_dict(run, *, timed_out: bool = False, is_stale: bool = False) -> dict:
    """Public projection of a (live-hydrated) :class:`SwarmRun`.

    ``timed_out`` flips on only for the ``run_swarm`` wait-budget path. It does
    not change the run's actual status — callers can still see ``running`` and
    fetch the final report later via :func:`get_run_result`.

    ``is_stale`` is a read-only signal: ``True`` means the run is still
    ``running`` but its events.jsonl has been silent past the per-run
    threshold. No disk state is changed by setting this — the explicit
    :func:`reap_stale_runs` tool is what finalizes a stale run.
    """
    from src.swarm.serialization import run_level_error, serialize_task

    return {
        "run_id": run.id,
        "status": run.status.value,
        "preset": run.preset_name,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "error": run_level_error(run),
        "tasks": [serialize_task(t) for t in run.tasks],
        "final_report": run.final_report,
        "total_input_tokens": run.total_input_tokens,
        "total_output_tokens": run.total_output_tokens,
        "timed_out": timed_out,
        "is_stale": is_stale,
    }


def _build_run_payload(store, run_id: str, preset_name: str | None, *, timed_out: bool) -> dict:
    """Reconcile + project a run for the MCP response.

    Used by ``run_swarm`` (polling + start_only). Returns a normal payload on
    success and a ``{"status": "error", ...}`` envelope when the run record
    disappears (mid-run directory wipe / sandbox eviction).
    """
    run = store.load_run(run_id)
    if run is None:
        return {"status": "error", "error": "Run record lost", "run_id": run_id}
    reconciled = store.reconcile_run(run, write=True)
    payload = _run_to_dict(
        reconciled,
        timed_out=timed_out,
        is_stale=store.is_run_stale(reconciled),
    )
    if preset_name:
        payload["preset"] = preset_name
    return payload


@mcp.tool
def get_swarm_status(run_id: str) -> str:
    """Get the current status of a swarm run.

    Returns status, task progress, token usage, and an ``is_stale`` flag for
    the specified run. Use this to poll a long-running swarm without blocking.

    Args:
        run_id: The run ID returned by run_swarm.
    """
    store = _get_swarm_store()
    try:
        run = store.load_run(run_id)
    except ValueError as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
    if run is None:
        return json.dumps({"status": "error", "error": f"Run {run_id} not found"}, ensure_ascii=False)
    reconciled = store.reconcile_run(run, write=True)
    return json.dumps(
        _run_to_dict(reconciled, is_stale=store.is_run_stale(reconciled)),
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool
def get_run_result(run_id: str) -> str:
    """Get the final report and task summaries of a swarm run.

    Reconciles the run on read: an orphaned ``running`` run whose host
    process exited will be transitioned to its real terminal status
    (``completed`` / ``failed`` / ``cancelled`` derived from the task
    statuses), so the caller never sees a permanent zombie.

    Args:
        run_id: The run ID returned by run_swarm.
    """
    store = _get_swarm_store()
    try:
        run = store.load_run(run_id)
    except ValueError as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
    if run is None:
        return json.dumps({"status": "error", "error": f"Run {run_id} not found"}, ensure_ascii=False)
    reconciled = store.reconcile_run(run, write=True)
    payload = _run_to_dict(reconciled, is_stale=store.is_run_stale(reconciled))
    payload["ready"] = payload["status"] in {"completed", "failed", "cancelled"}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool
def list_runs(limit: int = 20) -> str:
    """List recent swarm runs sorted by creation time (newest first).

    Each row includes task counts and an ``is_stale`` flag so callers can
    spot abandoned runs without a follow-up status call.

    Args:
        limit: Maximum number of runs to return (default 20).
    """
    store = _get_swarm_store()
    runs = store.list_runs(limit=limit)
    items = []
    for run in runs:
        # write=True so a zombie listed alongside live runs gets finalized;
        # the cost is bounded by ``limit`` (default 20) and most rows are
        # already terminal — reconcile is a no-op for those.
        reconciled = store.reconcile_run(run, write=True)
        counts = {"total": len(reconciled.tasks)}
        for t in reconciled.tasks:
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        items.append(
            {
                "run_id": reconciled.id,
                "preset": reconciled.preset_name,
                "status": reconciled.status.value,
                "is_stale": store.is_run_stale(reconciled),
                "created_at": reconciled.created_at,
                "completed_at": reconciled.completed_at,
                "task_counts": counts,
                "total_input_tokens": reconciled.total_input_tokens,
                "total_output_tokens": reconciled.total_output_tokens,
            }
        )
    return json.dumps(items, ensure_ascii=False, indent=2)


@mcp.tool
def reap_stale_runs() -> str:
    """Mark every ``running`` run whose host process died as ``failed``.

    Walks the swarm store, applies the per-run stale threshold, and
    finalizes any run that has gone silent past it (writes ``run.json`` +
    ``tasks/*.json`` + appends a ``run_reaped`` event). Already-terminal
    runs and still-alive runs are left untouched.

    Returns:
        JSON list of reaped run IDs (empty when nothing was stale).
    """
    store = _get_swarm_store()
    reaped = store.reap_stale_running_runs()
    return json.dumps({"reaped": reaped}, ensure_ascii=False, indent=2)


@mcp.tool
def retry_run(run_id: str) -> str:
    """Retry a failed, stale, or cancelled swarm run.

    Re-launches a brand-new run with the same preset and variables as the
    original; the original run is left untouched as a record. Use this after
    spotting a ``failed`` or stale run via ``list_runs``. A still-``running``
    run cannot be retried — cancel or reap it first.

    Args:
        run_id: ID of the run to retry (from ``list_runs`` / ``get_swarm_status``).

    Returns:
        JSON payload for the newly created run (``run_id`` / ``status`` /
        ``preset`` …), or an ``error`` object if the run is missing or active.
    """
    from src.config import load_swarm_agent_config
    from src.swarm.models import RunStatus
    from src.swarm.runtime import SwarmRuntime

    store = _get_swarm_store()
    try:
        loaded = store.load_run(run_id)
    except ValueError as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
    if loaded is None:
        return json.dumps({"status": "error", "error": f"Run {run_id} not found"}, ensure_ascii=False)

    # Reconcile first so a zombie "running" run whose host died is demoted
    # before we gate on status; only a genuinely active run blocks retry.
    reconciled = store.reconcile_run(loaded, write=True)
    if reconciled.status == RunStatus.running:
        return json.dumps(
            {"status": "error", "error": "Cannot retry a running run. Cancel or reap it first."},
            ensure_ascii=False,
        )

    agent_config = load_swarm_agent_config()
    runtime = SwarmRuntime(store=store, agent_config=agent_config)
    try:
        new_run = runtime.start_run(
            reconciled.preset_name,
            reconciled.user_vars or {},
            include_shell_tools=_include_shell_tools,
        )
    except FileNotFoundError as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
    except ValueError as exc:
        return json.dumps({"status": "error", "error": f"DAG validation failed: {exc}"}, ensure_ascii=False)

    return json.dumps(
        _build_run_payload(store, new_run.id, new_run.preset_name, timed_out=False),
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Trade journal tool
# ---------------------------------------------------------------------------


@mcp.tool
def analyze_trade_journal(
    file_path: str,
    analysis_type: str = "full",
    filter_expr: str = "",
) -> str:
    """Analyze a user's trade journal (CSV/Excel broker export) and return
    a trading profile plus behavior diagnostics.

    Parses 同花顺 / 东方财富 / 富途 / generic formats (encoding auto-detected).
    Output (JSON):
      - profile: holding days, frequency, win rate, PnL ratio, top symbols,
                 market distribution, hourly distribution
      - behaviors: disposition effect, overtrading, chasing momentum,
                   anchoring (each with severity + numeric evidence)

    Args:
        file_path: Absolute path to the uploaded CSV/Excel file.
        analysis_type: "full" | "profile" | "behavior" | "strategy".
        filter_expr: Optional filter (e.g. "2026-01 to 2026-03",
                     "symbol=600519.SH", "market=china_a").
    """
    registry = _get_registry()
    return registry.execute(
        "analyze_trade_journal",
        {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "filter_expr": filter_expr,
        },
    )


# ---------------------------------------------------------------------------
# Shadow Account tools (4)
# ---------------------------------------------------------------------------


@mcp.tool
def extract_shadow_strategy(
    journal_path: str,
    min_support: int = 3,
    max_rules: int = 5,
) -> str:
    """Extract a Shadow Account profile (3-5 human-readable if-then rules)
    from the user's profitable roundtrips in a trade journal.

    Run `analyze_trade_journal` first if the journal hasn't been parsed.
    Returns shadow_id + rules preview. Profile persists to
    ~/.vibe-trading/shadow_accounts/.

    Args:
        journal_path: Path to the CSV/Excel broker export.
        min_support: Minimum profitable roundtrips required to back one rule.
        max_rules: Maximum rules to return (typically 3-5).
    """
    registry = _get_registry()
    return registry.execute(
        "extract_shadow_strategy",
        {
            "journal_path": journal_path,
            "min_support": min_support,
            "max_rules": max_rules,
        },
    )


@mcp.tool
def run_shadow_backtest(
    shadow_id: str,
    window_start: str = "",
    window_end: str = "",
    markets: list[str] | None = None,
    journal_path: str = "",
) -> str:
    """Run a multi-market backtest (A股/港股/美股/crypto) on a Shadow Account
    profile and compute delta-PnL attribution vs the user's realized trades.

    Requires `extract_shadow_strategy` to have run first.

    Args:
        shadow_id: ID returned by extract_shadow_strategy.
        window_start: ISO date, default today-1y.
        window_end: ISO date, default today.
        markets: Subset of ["china_a", "hk", "us", "crypto"], default all four.
        journal_path: Original journal path (enables attribution), optional.
    """
    registry = _get_registry()
    params: dict[str, Any] = {"shadow_id": shadow_id}
    if window_start:
        params["window_start"] = window_start
    if window_end:
        params["window_end"] = window_end
    if markets:
        params["markets"] = markets
    if journal_path:
        params["journal_path"] = journal_path
    return registry.execute("run_shadow_backtest", params)


@mcp.tool
def render_shadow_report(
    shadow_id: str,
    include_today_signals: bool = True,
    window_start: str = "",
    window_end: str = "",
    journal_path: str = "",
) -> str:
    """Render the Shadow Account HTML/PDF report (8 sections + charts) for
    a shadow_id. If no cached backtest, one is run automatically.

    Args:
        shadow_id: Shadow Account ID.
        include_today_signals: Include today's market scan section.
        window_start: Optional backtest window override.
        window_end: Optional backtest window override.
        journal_path: Original journal path (for attribution), optional.
    """
    registry = _get_registry()
    params: dict[str, Any] = {
        "shadow_id": shadow_id,
        "include_today_signals": include_today_signals,
    }
    if window_start:
        params["window_start"] = window_start
    if window_end:
        params["window_end"] = window_end
    if journal_path:
        params["journal_path"] = journal_path
    return registry.execute("render_shadow_report", params)


@mcp.tool
def scan_shadow_signals(
    shadow_id: str,
    date: str = "",
    per_market: int = 3,
) -> str:
    """List today's symbols that match the Shadow Account's entry cadence
    (research use only — not a trade recommendation).

    Args:
        shadow_id: Shadow Account ID.
        date: ISO YYYY-MM-DD target date, default today.
        per_market: Max signals per market.
    """
    registry = _get_registry()
    params: dict[str, Any] = {"shadow_id": shadow_id, "per_market": per_market}
    if date:
        params["date"] = date
    return registry.execute("scan_shadow_signals", params)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Entry point for `vibe-trading-mcp` CLI command."""
    global _include_shell_tools, _registry
    import argparse

    parser = argparse.ArgumentParser(description="Vibe-Trading MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport (default: stdio)")
    parser.add_argument("--port", type=int, default=8900, help="SSE port (only used with --transport sse)")
    args = parser.parse_args()
    _include_shell_tools = True if args.transport == "stdio" else _env_shell_tools_enabled()
    _registry = None
    _get_registry()  # pre-warm: avoids deadlock when first tools/call lazy-inits inside FastMCP worker thread

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
