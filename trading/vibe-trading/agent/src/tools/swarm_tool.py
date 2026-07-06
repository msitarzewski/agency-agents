"""SwarmTool: tool for the main agent to invoke a swarm multi-agent team.

The user provides a natural-language prompt; the tool auto-selects the best preset and extracts variables.
Blocks synchronously until the run completes and returns a JSON summary.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 5
_MAX_WAIT_SECONDS = int(os.getenv("SWARM_TIMEOUT", "1800"))

# Preset matching: (preset_name, keyword_patterns, weight_boost). Patterns match user intent (EN + ZH).
_PRESET_KEYWORDS: list[tuple[str, list[str], float]] = [
    (
        "global_allocation_committee",
        [
            r"cross[- ]?market",
            r"global\s+alloc",
            "multi[- ]asset",
            "三市场",
            "全球配置",
            "资产配置",
            "港美.*A股",
            "A股.*加密",
            "加密.*A股",
            "多市场",
        ],
        1.0,
    ),
    (
        "risk_committee",
        [
            r"risk\s+audit",
            "drawdown",
            r"tail\s+risk",
            r"stress\s+test",
            r"\bVaR\b",
            "风控",
            "风险审计",
            "回撤",
            "尾部风险",
            "压力测试",
            "风险评估",
        ],
        1.0,
    ),
    (
        "quant_strategy_desk",
        [
            r"\bquant\b",
            "alpha",
            "factor",
            "backtest",
            "多因子",
            "量化策略",
            "因子",
            "选股",
            "策略.*回测",
        ],
        1.0,
    ),
    (
        "equity_research_team",
        [
            "equity research",
            "stock research",
            "研报",
            "研究报告",
            "行业分析",
            "个股分析",
            "投资分析",
            "macro.*sector",
            "投资机会",
        ],
        0.85,
    ),
    (
        "factor_research_committee",
        [
            r"factor\s+research",
            r"\bIC\b",
            "ICIR",
            "因子委员会",
            "因子研究",
        ],
        0.9,
    ),
    (
        "event_driven_task_force",
        [
            r"M&A",
            "merger",
            "insider",
            r"earnings\s+surprise",
            "事件驱动",
            "并购",
            "财报",
        ],
        0.9,
    ),
    (
        "etf_allocation_desk",
        [
            r"\bETF\b",
            r"index\s+fund",
            "指数基金",
            "ETF配置",
        ],
        0.9,
    ),
    (
        "derivatives_strategy_desk",
        [
            r"\boptions?\b",
            r"\bcall\s+options?\b",
            r"\bput\s+options?\b",
            r"\bGreeks?\b",
            r"implied\s+vol",
            r"\bIV\b",
            "期权",
            "衍生品",
        ],
        0.9,
    ),
    (
        "crypto_research_lab",
        [
            r"\bBTC\b",
            r"\bETH\b",
            r"\bSOL\b",
            "crypto",
            "bitcoin",
            "加密",
            "数字货币",
        ],
        0.95,
    ),
    (
        "credit_research_team",
        [
            r"credit\s+bond",
            "LGFV",
            r"\bYTM\b",
            "利差",
            "信用债",
            "城投",
        ],
        0.9,
    ),
    (
        "convertible_bond_team",
        [
            "convertible",
            "可转债",
            r"\bCB\b",
        ],
        0.9,
    ),
    (
        "fundamental_research_team",
        [
            "fundamental",
            r"deep\s+dive",
            "财务",
            "基本面",
        ],
        0.85,
    ),
    (
        "commodity_research_team",
        [
            "commodity",
            "crude",
            "gold",
            "copper",
            r"iron\s+ore",
            "商品",
            "原油",
            "黄金",
        ],
        0.9,
    ),
    (
        "fund_selection_panel",
        [
            r"\bFOF\b",
            r"mutual\s+fund",
            "基金筛选",
            "选基",
        ],
        0.85,
    ),
    (
        "social_alpha_team",
        [
            r"social\s+media",
            "twitter",
            "reddit",
            "社媒",
            "舆情",
        ],
        0.85,
    ),
    (
        "geopolitical_war_room",
        [
            "geopolitical",
            r"war\s+risk",
            "sanction",
            "地缘",
            "危机场景",
        ],
        0.9,
    ),
    (
        "pairs_research_lab",
        [
            r"pairs\s+trading",
            "cointegration",
            "配对",
            "统计套利",
        ],
        0.9,
    ),
    (
        "investment_committee",
        [
            r"investment\s+committee",
            "投委会",
            "投资决策",
        ],
        0.85,
    ),
    (
        "macro_strategy_forum",
        [
            r"\bFed\b",
            r"\bCPI\b",
            r"\bPMI\b",
            "macro",
            "货币政策",
            "宏观",
        ],
        0.9,
    ),
    (
        "statistical_arbitrage_desk",
        [
            r"statistical\s+arbitrage",
            r"stat\s+arb",
            "统计套利",
        ],
        0.9,
    ),
    (
        "sentiment_intelligence_team",
        [
            "sentiment",
            r"fear\s+and\s+greed",
            "情绪",
            "恐慌",
        ],
        0.85,
    ),
    (
        "technical_analysis_panel",
        [
            r"technical\s+analysis",
            r"\bRSI\b",
            r"\bMACD\b",
            "技术分析",
            "K线",
        ],
        0.85,
    ),
    (
        "sector_rotation_team",
        [
            r"sector\s+rotation",
            "板块轮动",
            "行业轮动",
        ],
        0.85,
    ),
    (
        "portfolio_review_board",
        [
            r"portfolio\s+review",
            "组合复盘",
            "业绩归因",
        ],
        0.85,
    ),
    (
        "ml_quant_lab",
        [
            r"\bML\b",
            r"machine\s+learning",
            "LSTM",
            "XGBoost",
            "机器学习",
            "深度学习",
        ],
        0.9,
    ),
]

# Market labels used in YAML templates (English, compatible with {market} placeholders).
_MARKET_PATTERNS: list[tuple[str, list[str]]] = [
    ("A-shares", [r"A股", r"a股", "沪深", "上证", "深证", "创业板", "科创板", "中证", r"\bCSI\b"]),
    ("crypto", ["加密", r"\bcrypto\b", r"\bBTC\b", r"\bETH\b", "币", "USDT", "数字货币"]),
    ("Hong Kong", ["港股", "恒生", r"H股", "港交所", r"\.HK\b"]),
    ("US", ["美股", "纳斯达克", "标普", "道琼斯", r"S&P", r"\.US\b"]),
]

# Risk tolerance for global_allocation_committee (English).
_RISK_PATTERNS: list[tuple[str, list[str]]] = [
    ("conservative", ["保守", r"低风险", "稳健偏保守", r"conservative"]),
    ("moderate", ["稳健", "中等风险", r"moderate", r"balanced"]),
    ("aggressive", ["激进", "高风险", "进取", r"aggressive"]),
]


_STRATEGY_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    ("low-price", [r"\blow[- ]price\b", r"\bcheap\b", r"\bdiscount\b", r"\blow premium\b"]),
    ("dual-low", [r"\bdual[- ]low\b", r"\bdouble[- ]low\b"]),
    ("high-convexity", [r"\bhigh[- ]convexity\b", r"\bconvexity\b"]),
    ("rotation", [r"\brotation\b", r"\brotate\b", r"\brebalance\b"]),
]

_TARGET_VARIABLE_PATTERNS: list[tuple[str, list[str]]] = [
    ("volatility", [r"\bvolatility\b", r"\bvol\b", r"\bvariance\b", r"\brisk\b"]),
    ("direction", [r"\bdirection(?:al)?\b", r"\bup[- ]down\b", r"\bclassification\b"]),
    ("return", [r"\breturns?\b", r"\balpha\b", r"\bpredict\b", r"\bforecast\b"]),
]

_REVIEW_PERIOD_PATTERNS: list[tuple[str, list[str]]] = [
    ("monthly", [r"\bmonthly\b", r"\bmonth(?:ly)?\b"]),
    ("quarterly", [r"\bquarter(?:ly)?\b", r"\bq[1-4]\b"]),
]

_SECTOR_PATTERNS: list[tuple[str, list[str]]] = [
    ("banks", [r"\bbank(?:s|ing)?\b", r"\bfinancials?\b"]),
    ("consumer", [r"\bconsumer\b", r"\bretail\b", r"\bstaples\b", r"\bdiscretionary\b"]),
    ("semiconductors", [r"\bsemi(?:s|conductors?)?\b", r"\bchip(?:s)?\b"]),
    ("technology", [r"\btech(?:nology)?\b", r"\bsoftware\b", r"\binternet\b"]),
    ("energy", [r"\benergy\b", r"\boil\b", r"\bgas\b", r"\bpower\b"]),
    ("healthcare", [r"\bhealth ?care\b", r"\bbiotech\b", r"\bpharma\b"]),
    ("industrials", [r"\bindustrial(?:s)?\b", r"\bmanufacturing\b"]),
    ("real estate", [r"\breal estate\b", r"\bproperty\b", r"\breit(?:s)?\b"]),
    ("utilities", [r"\butilit(?:y|ies)\b"]),
    ("materials", [r"\bmaterials?\b", r"\bmetals?\b", r"\bmining\b"]),
]


def _match_preset(prompt: str) -> str:
    """Match user prompt to best preset using keyword scoring.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Best matching preset name.
    """
    normalized_prompt = re.sub(r"[\s-]+", "_", prompt.strip().lower())
    for preset_name, _, _ in _PRESET_KEYWORDS:
        if re.search(rf"(?<![a-z0-9]){re.escape(preset_name)}(?![a-z0-9])", normalized_prompt):
            return preset_name

    scores: dict[str, float] = {}
    for preset_name, keywords, boost in _PRESET_KEYWORDS:
        score = 0.0
        for kw in keywords:
            if re.search(kw, prompt, re.IGNORECASE):
                score += boost
        scores[preset_name] = score

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] > 0:
        return best

    return "equity_research_team"


_PRESET_NAMES = {preset_name for preset_name, _, _ in _PRESET_KEYWORDS}
_CONTINUATION_PATTERNS = (
    r"^\s*continue\b",
    r"^\s*resume\b",
    r"^\s*finish\b",
    r"\bcontinue\s+(?:and\s+)?finish\b",
    r"\bcontinue\s+from\b",
    r"\bfinish\s+(?:the\s+)?report\b",
    r"\bcomplete\s+(?:the\s+)?report\b",
    r"\bpick\s+up\s+from\b",
    r"^\s*继续",
    r"^\s*接着",
)


def _normalize_preset_name(value: str) -> str | None:
    """Normalize an explicit preset name and validate it against bundled presets."""
    normalized = re.sub(r"[\s-]+", "_", value.strip().lower())
    return normalized if normalized in _PRESET_NAMES else None


def _has_preset_signal(prompt: str) -> bool:
    """Return whether prompt contains an explicit preset name or routing keyword."""
    normalized_prompt = re.sub(r"[\s-]+", "_", prompt.strip().lower())
    for preset_name, _, _ in _PRESET_KEYWORDS:
        if re.search(rf"(?<![a-z0-9]){re.escape(preset_name)}(?![a-z0-9])", normalized_prompt):
            return True
    for _, keywords, _ in _PRESET_KEYWORDS:
        for kw in keywords:
            if re.search(kw, prompt, re.IGNORECASE):
                return True
    return False


def _looks_like_continuation_prompt(prompt: str) -> bool:
    """Detect prompts that refer to prior work instead of a fresh swarm task."""
    return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in _CONTINUATION_PATTERNS)


def _resolve_preset(prompt: str, explicit_preset: str | None = None) -> tuple[str | None, str | None]:
    """Resolve the preset to run, returning an error string when ambiguous."""
    if explicit_preset:
        preset = _normalize_preset_name(explicit_preset)
        if preset is None:
            available = ", ".join(sorted(_PRESET_NAMES))
            return None, f"Unknown preset_name '{explicit_preset}'. Available presets: {available}"
        return preset, None

    if _looks_like_continuation_prompt(prompt) and not _has_preset_signal(prompt):
        return (
            None,
            "Ambiguous continuation swarm prompt. Reuse the previous swarm result, "
            "or call run_swarm with preset_name and the original full request. "
            "Refusing to auto-route this continuation to equity_research_team.",
        )

    return _match_preset(prompt), None


def _extract_market(prompt: str) -> str:
    """Extract target market label from prompt.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Market label for template variables, default A-shares.
    """
    for market, patterns in _MARKET_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return market
    return "A-shares"


def _extract_risk_tolerance(prompt: str) -> str:
    """Extract risk tolerance from prompt (English labels).

    Args:
        prompt: User's natural language prompt.

    Returns:
        conservative | moderate | aggressive.
    """
    for level, patterns in _RISK_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return level
    return "moderate"


def _risk_to_etf_profile(risk: str) -> str:
    """Map tolerance to etf_allocation_desk risk_profile values."""
    return {"conservative": "conservative", "moderate": "balanced", "aggressive": "aggressive"}.get(risk, "balanced")


def _extract_strategy_type(prompt: str) -> str:
    """Extract convertible bond strategy type from prompt.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Strategy type label used by the convertible bond preset.
    """
    for strategy_type, patterns in _STRATEGY_TYPE_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return strategy_type
    return "rotation"


def _extract_target_variable(prompt: str) -> str:
    """Extract ML prediction target from prompt.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Prediction target label for ml_quant_lab.
    """
    for target_variable, patterns in _TARGET_VARIABLE_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return target_variable
    return "return"


def _extract_review_period(prompt: str) -> str:
    """Extract portfolio review cadence from prompt.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Review cadence label for portfolio_review_board.
    """
    for review_period, patterns in _REVIEW_PERIOD_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return review_period
    return "quarterly"


def _extract_sector(prompt: str) -> str:
    """Extract sector constraint from prompt.

    Args:
        prompt: User's natural language prompt.

    Returns:
        Sector filter value, or empty string for full-market scans.
    """
    broad_market_patterns = [
        r"\bfull market\b",
        r"\bbroad market\b",
        r"\ball sectors\b",
        r"\bacross sectors\b",
    ]
    for pat in broad_market_patterns:
        if re.search(pat, prompt, re.IGNORECASE):
            return ""

    for sector, patterns in _SECTOR_PATTERNS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return sector
    return ""


def _snippet(prompt: str, max_len: int = 240) -> str:
    """Trim prompt for auxiliary fields."""
    s = prompt.strip()
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _build_variables(preset_name: str, prompt: str) -> dict[str, str]:
    """Build template variables from prompt for the matched preset.

    Args:
        preset_name: Matched preset name.
        prompt: User's original prompt.

    Returns:
        Dict of template variables required by the YAML preset.
    """
    market = _extract_market(prompt)
    risk = _extract_risk_tolerance(prompt)
    goal = prompt.strip()
    g = _snippet(goal, 2000)

    # Preset-specific variable sets (see agent/src/swarm/presets/*.yaml).
    builders: dict[str, dict[str, str]] = {
        "global_allocation_committee": {"goal": g, "risk_tolerance": risk},
        "equity_research_team": {"market": market, "goal": g},
        "quant_strategy_desk": {"market": market, "goal": g},
        "risk_committee": {"goal": g},
        "factor_research_committee": {"market": market, "factor_type": "value"},
        "event_driven_task_force": {"market": market, "event_type": "all types"},
        "etf_allocation_desk": {"risk_profile": _risk_to_etf_profile(risk), "market": market},
        "derivatives_strategy_desk": {"target": g, "view": "neutral"},
        "crypto_research_lab": {"target": "BTC, ETH, SOL", "timeframe": "medium-term 1-3 months"},
        "credit_research_team": {"target": g, "market": "China credit bonds"},
        "convertible_bond_team": {
            "market": "A-share convertible bonds",
            "goal": g,
            "strategy_type": _extract_strategy_type(prompt),
        },
        "fundamental_research_team": {"target": g, "market": market},
        "commodity_research_team": {"commodity": "gold", "horizon": "3 months"},
        "fund_selection_panel": {"fund_type": "equity", "goal": g},
        "social_alpha_team": {"target": g, "timeframe": "daily"},
        "geopolitical_war_room": {"crisis": g, "market": market},
        "pairs_research_lab": {"market": market, "sector": _extract_sector(prompt)},
        "investment_committee": {"target": g, "market": market},
        "macro_strategy_forum": {"market": market, "horizon": "quarterly"},
        "statistical_arbitrage_desk": {"market": market, "goal": g, "sector": _extract_sector(prompt)},
        "sentiment_intelligence_team": {"market": market, "timeframe": "daily"},
        "technical_analysis_panel": {"target": g, "timeframe": "daily"},
        "sector_rotation_team": {"market": market, "goal": g},
        "portfolio_review_board": {"portfolio": g, "review_period": _extract_review_period(prompt), "goal": g},
        "ml_quant_lab": {"market": market, "target_variable": _extract_target_variable(prompt), "goal": g},
    }

    return builders.get(preset_name, {"market": market, "goal": g})


class SwarmTool(BaseTool):
    """Launch a swarm multi-agent team to execute complex tasks.

    Accepts a natural-language prompt, auto-selects the best preset,
    and blocks synchronously until the swarm run completes or times out.
    """

    name = "run_swarm"
    description = (
        "Run a multi-agent swarm team for complex analysis tasks. "
        "Provide a natural language prompt and, when known, an explicit preset_name from agent/src/swarm/presets "
        "(e.g. equity_research_team, quant_strategy_desk, global_allocation_committee, risk_committee) "
        "so follow-up/continuation prompts do not lose routing context. "
        "Example: run_swarm(prompt='Analyze A-share new energy opportunities for Q2 2026', preset_name='equity_research_team')"
    )
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Natural language description of the analysis task.",
            },
            "preset_name": {
                "type": "string",
                "description": "Optional explicit swarm preset name when the user named one or this is a continuation.",
            },
        },
        "required": ["prompt"],
    }
    is_readonly = False
    repeatable = True  # loop.py dedups by tool name; each prompt is a distinct run (#42)

    def __init__(
        self,
        *,
        include_shell_tools: bool = False,
        event_callback: Any | None = None,
    ) -> None:
        """Initialize the swarm launcher.

        Args:
            include_shell_tools: Whether worker registries may include shell
                execution tools requested by presets.
            event_callback: Optional session event bridge used by the web chat.
        """
        self.include_shell_tools = include_shell_tools
        self._event_callback = event_callback

    def _emit_session_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Forward swarm status to the hosting session SSE channel if present."""
        if self._event_callback is None:
            return
        try:
            self._event_callback(event_type, data)
        except Exception:
            logger.warning("Failed to forward %s to session event stream", event_type, exc_info=True)

    def execute(self, **kwargs: Any) -> str:
        """Start a swarm run: auto-match preset, extract variables, wait for completion.

        Args:
            **kwargs: Must include prompt (str).

        Returns:
            JSON string with status, preset, variables, final_report, tasks, token_usage.
        """
        prompt = kwargs.get("prompt", "")

        if not prompt:
            return json.dumps(
                {"status": "error", "error": "Missing 'prompt' parameter"},
                ensure_ascii=False,
            )

        preset, preset_error = _resolve_preset(prompt, kwargs.get("preset_name"))
        if preset_error:
            return json.dumps(
                {"status": "error", "error": preset_error},
                ensure_ascii=False,
            )
        assert preset is not None
        variables = _build_variables(preset, prompt)

        logger.info(
            "SwarmTool: resolved preset=%s, variables=%s from prompt: %s",
            preset,
            variables,
            prompt[:100],
        )

        from src.config import load_swarm_agent_config
        from src.swarm.runtime import SwarmRuntime
        from src.swarm.store import SwarmStore

        swarm_base_dir = Path(__file__).resolve().parents[2] / ".swarm" / "runs"
        swarm_base_dir.mkdir(parents=True, exist_ok=True)
        store = SwarmStore(base_dir=swarm_base_dir)
        # Boot-time / operator-trusted: even when reached via the in-process
        # agent tool, the config path is resolved from disk / env, never from
        # the calling LLM's prompt (R-06).
        agent_config = load_swarm_agent_config()
        runtime = SwarmRuntime(
            store=store,
            max_workers=int(os.getenv("SWARM_MAX_WORKERS", "4")),
            agent_config=agent_config,
        )

        pending_live_events: list[dict[str, Any]] = []
        run_id_holder: dict[str, str | None] = {"run_id": None}

        try:
            def _live_callback(event: Any) -> None:
                payload = event.model_dump()
                current_run_id = run_id_holder["run_id"]
                if current_run_id is None:
                    pending_live_events.append(payload)
                    return
                self._emit_session_event(
                    "swarm.event",
                    {"run_id": current_run_id, "event": payload},
                )

            run = runtime.start_run(
                preset,
                variables,
                live_callback=_live_callback if self._event_callback is not None else None,
                include_shell_tools=self.include_shell_tools,
            )
        except FileNotFoundError as exc:
            return json.dumps(
                {"status": "error", "error": f"Preset not found: {exc}"},
                ensure_ascii=False,
            )
        except ValueError as exc:
            return json.dumps(
                {"status": "error", "error": f"Invalid DAG: {exc}"},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps(
                {"status": "error", "error": f"Failed to start swarm: {exc}"},
                ensure_ascii=False,
            )

        run_id = run.id
        run_id_holder["run_id"] = run_id
        logger.info("SwarmTool: started run %s (preset=%s)", run_id, preset)
        self._emit_session_event(
            "swarm.started",
            {
                "run_id": run_id,
                "preset": preset,
                "variables": variables,
                "status": run.status.value,
                "agents": [agent.model_dump() for agent in run.agents],
                "tasks": [task.model_dump() for task in run.tasks],
            },
        )
        for event_payload in pending_live_events:
            self._emit_session_event(
                "swarm.event",
                {"run_id": run_id, "event": event_payload},
            )
        pending_live_events.clear()

        t0 = time.monotonic()
        while time.monotonic() - t0 < _MAX_WAIT_SECONDS:
            time.sleep(_POLL_INTERVAL_SECONDS)

            loaded = store.load_run(run_id)
            if loaded is None:
                return json.dumps(
                    {"status": "error", "error": f"Run {run_id} disappeared"},
                    ensure_ascii=False,
                )

            reconciled = store.reconcile_run(loaded, write=True)
            if reconciled.status.value in ("completed", "failed", "cancelled"):
                return _format_result(reconciled, preset, variables)

        # Wait budget elapsed but the run is still in flight. Do NOT cancel —
        # the daemon thread keeps working and the agent can decide to wait
        # more (re-invoke with the returned run_id) or hand off partial state
        # to the user. Cancelling here used to throw away minutes of LLM cost
        # whenever a preset legitimately ran past the budget.
        loaded = store.load_run(run_id)
        if loaded is not None:
            return _format_result(
                store.reconcile_run(loaded, write=True), preset, variables, timed_out=True
            )

        return json.dumps(
            {"status": "timeout", "error": f"Swarm run {run_id} timed out after {_MAX_WAIT_SECONDS}s"},
            ensure_ascii=False,
        )


def _format_result(
    run: Any,
    preset: str,
    variables: dict[str, str],
    timed_out: bool = False,
) -> str:
    """Format a SwarmRun into a JSON result string.

    Args:
        run: SwarmRun instance.
        preset: Matched preset name.
        variables: Extracted variables.
        timed_out: Whether the run was terminated due to timeout.

    Returns:
        JSON string with run status, report, task summaries, and token usage.
    """
    from src.swarm.serialization import run_level_error, serialize_task

    task_summaries = [serialize_task(task) for task in run.tasks]

    # ``timed_out`` only means the SwarmTool's wait budget elapsed — the run
    # itself is still progressing in the background. Surface the run's real
    # status so a downstream agent can re-invoke with the run_id (or end its
    # turn with a "still working" message) instead of treating it as failure.
    result = {
        "status": run.status.value,
        "wait_budget_exhausted": timed_out,
        "run_id": run.id,
        "preset": preset,
        "auto_variables": variables,
        "final_report": run.final_report or "",
        "error": run_level_error(run),
        "tasks": task_summaries,
        "token_usage": {
            "total_input_tokens": run.total_input_tokens,
            "total_output_tokens": run.total_output_tokens,
        },
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
