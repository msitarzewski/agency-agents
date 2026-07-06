"""Startup preflight checks for data sources and LLM provider.

Runs connectivity checks at startup and prints a status table.
Non-critical failures are warnings (degraded functionality),
LLM provider failure is critical (blocks startup).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.util import find_spec
from typing import List, Optional

from rich.console import Console
from rich.table import Table


@dataclass(frozen=True)
class CheckResult:
    """Result of a single preflight check."""

    name: str
    status: str  # "ready", "error", "not_configured", "skipped"
    message: str
    impact: str  # what breaks if this fails
    critical: bool = False


def _check_llm_provider() -> CheckResult:
    """Verify LLM provider connectivity."""
    from src.providers.llm import _ensure_dotenv, _sync_provider_env, provider_diagnostics

    _ensure_dotenv()
    provider = os.getenv("LANGCHAIN_PROVIDER", "").strip()
    model = os.getenv("LANGCHAIN_MODEL_NAME", "").strip()

    if not provider:
        return CheckResult(
            name="LLM Provider",
            status="not_configured",
            message="LANGCHAIN_PROVIDER not set in .env",
            impact="agent cannot function",
            critical=True,
        )
    if not model:
        return CheckResult(
            name=f"LLM ({provider})",
            status="not_configured",
            message="LANGCHAIN_MODEL_NAME not set in .env",
            impact="agent cannot function",
            critical=True,
        )

    _sync_provider_env()
    diagnostics = provider_diagnostics()
    base_url = os.getenv("OPENAI_BASE_URL", "") or os.getenv("OPENAI_API_BASE", "")
    proxy_label = ",".join(sorted(diagnostics.get("proxy", {}).keys())) or "none"
    diag_hint = (
        f"base={diagnostics['base_url']} "
        f"timeout={diagnostics['timeout_seconds']}s "
        f"retries={diagnostics['max_retries']} "
        f"proxy={proxy_label}"
    )

    if provider.lower() in {"openai-codex", "openai_codex"}:
        try:
            from src.providers.openai_codex import get_openai_codex_login_status

            token = get_openai_codex_login_status()
        except Exception as exc:
            return CheckResult(
                name=f"LLM ({provider})",
                status="error",
                message=f"OAuth status unavailable: {exc}",
                impact="run `vibe-trading provider login openai-codex`",
                critical=True,
            )
        if not token:
            return CheckResult(
                name=f"LLM ({provider})",
                status="not_configured",
                message="ChatGPT OAuth login not found",
                impact="run `vibe-trading provider login openai-codex`",
                critical=True,
            )
        account = getattr(token, "account_id", None) or "authenticated account"
        return CheckResult(
            name=f"LLM ({provider})",
            status="ready",
            message=f"{model} via ChatGPT OAuth ({account}) | {diag_hint}",
            impact="",
        )

    if not base_url:
        return CheckResult(
            name=f"LLM ({provider})",
            status="not_configured",
            message=f"base URL not set for {provider} | {diag_hint}",
            impact="agent cannot function",
            critical=True,
        )

    # Ping the base URL
    try:
        import requests

        # Strip /v1 suffix for health check, just test TCP+SSL
        ping_url = base_url.rstrip("/")
        if ping_url.endswith("/v1"):
            ping_url = ping_url[:-3]
        requests.get(ping_url, timeout=10)
        return CheckResult(
            name=f"LLM ({provider})",
            status="ready",
            message=f"{model} via {diagnostics['base_url']} | {diag_hint}",
            impact="",
        )
    except Exception as exc:
        return CheckResult(
            name=f"LLM ({provider})",
            status="error",
            message=f"{type(exc).__name__}: {exc} | {diag_hint}",
            impact="agent cannot function",
            critical=True,
        )


def _check_okx() -> CheckResult:
    """Check OKX public API reachability."""
    try:
        import requests

        resp = requests.get(
            "https://www.okx.com/api/v5/market/candles",
            params={"instId": "BTC-USDT", "bar": "1D", "limit": "1"},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == "0":
            return CheckResult(name="OKX API", status="ready", message="reachable", impact="")
        return CheckResult(
            name="OKX API",
            status="error",
            message=f"API returned code={data.get('code')}: {data.get('msg', '')}",
            impact="crypto backtest unavailable",
        )
    except Exception as exc:
        return CheckResult(
            name="OKX API",
            status="error",
            message=f"{type(exc).__name__}: {exc}",
            impact="crypto backtest unavailable",
        )


def _check_yfinance() -> CheckResult:
    """Check yfinance availability."""
    try:
        import yfinance  # noqa: F401
    except ImportError:
        return CheckResult(
            name="yfinance",
            status="skipped",
            message="package not installed",
            impact="US/HK equity backtest unavailable",
        )

    try:
        import yfinance as yf

        ticker = yf.Ticker("AAPL")
        info = ticker.fast_info
        if hasattr(info, "last_price") and info.last_price:
            return CheckResult(name="yfinance", status="ready", message="reachable", impact="")
        return CheckResult(name="yfinance", status="ready", message="reachable (no price data)", impact="")
    except Exception as exc:
        return CheckResult(
            name="yfinance",
            status="error",
            message=f"{type(exc).__name__}: {exc}",
            impact="US/HK equity backtest unavailable",
        )


def _check_tushare() -> CheckResult:
    """Check Tushare token configuration."""
    token = os.getenv("TUSHARE_TOKEN", "").strip()
    if not token or token == "your-tushare-token":
        return CheckResult(
            name="Tushare",
            status="not_configured",
            message="TUSHARE_TOKEN not set (optional)",
            impact="A-share data unavailable",
        )

    try:
        import tushare  # noqa: F401
    except ImportError:
        return CheckResult(
            name="Tushare",
            status="skipped",
            message="package not installed",
            impact="A-share data unavailable",
        )

    return CheckResult(name="Tushare", status="ready", message="token configured", impact="")


def _check_akshare() -> CheckResult:
    """Check akshare availability."""
    if find_spec("akshare") is None:
        return CheckResult(
            name="akshare",
            status="skipped",
            message="package not installed",
            impact="A-share/forex fallback unavailable",
        )
    return CheckResult(name="akshare", status="ready", message="installed", impact="")


def _check_content_filter_threshold() -> CheckResult:
    """Report the configured content filter warning threshold."""
    raw = os.getenv("CONTENT_FILTER_WARNING_THRESHOLD", "0.05")
    try:
        threshold = float(raw)
    except (TypeError, ValueError):
        threshold = 0.05
    return CheckResult(
        name="Content Filter Threshold",
        status="ready",
        message=f"{threshold:.0%} (set via CONTENT_FILTER_WARNING_THRESHOLD)",
        impact="",
    )


def _check_ccxt() -> CheckResult:
    """Check ccxt availability."""
    try:
        import ccxt  # noqa: F401
    except ImportError:
        return CheckResult(
            name="ccxt",
            status="skipped",
            message="package not installed",
            impact="crypto fallback unavailable",
        )
    return CheckResult(name="ccxt", status="ready", message="installed", impact="")


# -- Status icons and colors --------------------------------------------------

_STATUS_DISPLAY = {
    "ready": ("[green]OK[/green]", "green"),
    "error": ("[red]FAIL[/red]", "red"),
    "not_configured": ("[yellow]N/A[/yellow]", "yellow"),
    "skipped": ("[dim]SKIP[/dim]", "dim"),
}


def run_preflight(console: Optional[Console] = None) -> List[CheckResult]:
    """Run all preflight checks and print results.

    Args:
        console: Rich console for output. Creates one if not provided.

    Returns:
        List of check results.
    """
    if console is None:
        console = Console()

    checks = [
        _check_llm_provider,
        _check_okx,
        _check_yfinance,
        _check_tushare,
        _check_akshare,
        _check_ccxt,
        _check_content_filter_threshold,
    ]

    results: List[CheckResult] = []
    for check_fn in checks:
        results.append(check_fn())

    # Build display table
    table = Table(show_header=False, show_edge=False, padding=(0, 1), expand=False)
    table.add_column(width=4)   # icon
    table.add_column(width=18)  # name
    table.add_column()          # message

    for r in results:
        icon, color = _STATUS_DISPLAY[r.status]
        detail = r.message
        if r.status in ("error", "not_configured") and r.impact:
            detail = f"{r.message} ({r.impact})"
        table.add_row(icon, f"[{color}]{r.name}[/{color}]", f"[{color}]{detail}[/{color}]")

    console.print()
    console.print("[bold]Preflight Check[/bold]")
    console.print(table)

    has_critical = any(r.critical and r.status != "ready" for r in results)
    if has_critical:
        console.print("\n[bold red]Critical check failed - agent cannot start without a working LLM provider.[/bold red]")
        console.print("[dim]  See: agent/.env.example for configuration reference[/dim]")
    else:
        ready_count = sum(1 for r in results if r.status == "ready")
        console.print(f"\n[dim]{ready_count}/{len(results)} services ready[/dim]")

    console.print()
    return results
