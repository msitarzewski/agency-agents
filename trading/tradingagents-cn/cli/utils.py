import os
import re
from datetime import datetime
from typing import Dict, List

import questionary
from rich.console import Console

from cli.models import AnalystType
from tradingagents.llm_clients.model_catalog import get_model_options
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.stock_utils import StockUtils

logger = get_logger("cli")
console = Console()

ANALYST_ORDER = [
    ("市场分析师 | Market Analyst", AnalystType.MARKET),
    ("社交媒体分析师 | Social Media Analyst", AnalystType.SOCIAL),
    ("新闻分析师 | News Analyst", AnalystType.NEWS),
    ("基本面分析师 | Fundamentals Analyst", AnalystType.FUNDAMENTALS),
]

PROVIDER_OPTIONS: List[Dict[str, str]] = [
    {
        "label": "阿里百炼 (DashScope)",
        "key": "qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    {
        "label": "DeepSeek",
        "key": "deepseek",
        "base_url": "https://api.deepseek.com",
    },
    {
        "label": "OpenAI",
        "key": "openai",
        "base_url": "https://api.openai.com/v1",
    },
    {
        "label": "🔧 自定义OpenAI端点",
        "key": "custom_openai",
        "base_url": "custom",
    },
    {
        "label": "Anthropic",
        "key": "anthropic",
        "base_url": "https://api.anthropic.com/",
    },
    {
        "label": "Google",
        "key": "google",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
    },
    {
        "label": "OpenRouter",
        "key": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
    },
    {
        "label": "AiHubMix",
        "key": "aihubmix",
        "base_url": "https://aihubmix.com/v1",
    },
    {
        "label": "Ollama",
        "key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
    {
        "label": "智谱 GLM",
        "key": "glm",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
    },
]


def normalize_ticker_symbol(ticker: str) -> str:
    """Normalize ticker input while preserving exchange suffixes."""
    return ticker.strip().upper()


def get_ticker() -> str:
    """Prompt the user to enter a ticker symbol."""
    ticker = questionary.text(
        "请输入要分析的股票代码 | Enter the ticker symbol to analyze:",
        validate=lambda x: len(x.strip()) > 0 or "请输入有效的股票代码 | Please enter a valid ticker symbol.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not ticker:
        logger.info("\n[red]未提供股票代码，退出程序... | No ticker symbol provided. Exiting...[/red]")
        exit(1)

    return normalize_ticker_symbol(ticker)


def get_analysis_date() -> str:
    """Prompt the user to enter a date in YYYY-MM-DD format."""

    def validate_date(date_str: str) -> bool:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    date = questionary.text(
        "请输入分析日期 (YYYY-MM-DD) | Enter the analysis date (YYYY-MM-DD):",
        validate=lambda x: validate_date(x.strip())
        or "请输入有效的日期格式 YYYY-MM-DD | Please enter a valid date in YYYY-MM-DD format.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not date:
        logger.info("\n[red]未提供日期，退出程序... | No date provided. Exiting...[/red]")
        exit(1)

    return date.strip()


def select_analysts(ticker: str = None) -> List[AnalystType]:
    """Select analysts using an interactive checkbox."""
    available_analysts = ANALYST_ORDER.copy()

    if ticker and StockUtils.is_china_stock(ticker):
        available_analysts = [
            (display, value)
            for display, value in ANALYST_ORDER
            if value != AnalystType.SOCIAL
        ]
        console.print(f"[yellow]💡 检测到A股代码 {ticker}，社交媒体分析师不可用（国内数据源限制）[/yellow]")

    choices = questionary.checkbox(
        "选择您的分析师团队 | Select Your [Analysts Team]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in available_analysts
        ],
        instruction="\n- 按空格键选择/取消选择分析师 | Press Space to select/unselect analysts\n- 按 'a' 键全选/取消全选 | Press 'a' to select/unselect all\n- 按回车键完成选择 | Press Enter when done",
        validate=lambda x: len(x) > 0 or "您必须至少选择一个分析师 | You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        logger.info("\n[red]未选择分析师，退出程序... | No analysts selected. Exiting...[/red]")
        exit(1)

    return choices


def select_research_depth() -> int:
    """Select research depth using an interactive selection."""
    depth_options = [
        ("浅层 - 快速研究，少量辩论和策略讨论 | Shallow - Quick research, few debate rounds", 1),
        ("中等 - 中等程度，适度的辩论和策略讨论 | Medium - Moderate debate and strategy discussion", 3),
        ("深度 - 全面研究，深入的辩论和策略讨论 | Deep - Comprehensive research, in-depth debate", 5),
    ]

    choice = questionary.select(
        "选择您的研究深度 | Select Your [Research Depth]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in depth_options
        ],
        instruction="\n- 使用方向键导航 | Use arrow keys to navigate\n- 按回车键选择 | Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        logger.info("\n[red]未选择研究深度，退出程序... | No research depth selected. Exiting...[/red]")
        exit(1)

    return choice


def _prompt_custom_model_id() -> str:
    model_id = questionary.text(
        "请输入模型名称 | Enter model ID:",
        validate=lambda x: len(x.strip()) > 0 or "请输入模型名称 | Please enter a model ID.",
    ).ask()
    if not model_id:
        logger.info("\n[red]未输入模型名称，退出程序... | No model ID entered. Exiting...[/red]")
        exit(1)
    return model_id.strip()


def _select_model(provider: str, mode: str) -> str:
    options = get_model_options(provider, mode)
    choice = questionary.select(
        f"选择您的{'快速' if mode == 'quick' else '深度'}思考LLM引擎 | Select Your [{mode.title()}-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in options
        ],
        instruction="\n- 使用方向键导航 | Use arrow keys to navigate\n- 按回车键选择 | Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:green noinherit"),
                ("highlighted", "fg:green noinherit"),
                ("pointer", "fg:green noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        logger.info(f"\n[red]未选择{mode}模型，退出程序... | No {mode} model selected. Exiting...[/red]")
        exit(1)

    if choice == "custom":
        return _prompt_custom_model_id()

    return choice


def select_shallow_thinking_agent(provider: str) -> str:
    return _select_model(provider, "quick")


def select_deep_thinking_agent(provider: str) -> str:
    return _select_model(provider, "deep")


def select_llm_provider() -> tuple[str, str]:
    """Select the LLM provider using interactive selection."""
    choice = questionary.select(
        "选择您的LLM提供商 | Select your LLM Provider:",
        choices=[
            questionary.Choice(item["label"], value=(item["key"], item["base_url"]))
            for item in PROVIDER_OPTIONS
        ],
        default=(PROVIDER_OPTIONS[0]["key"], PROVIDER_OPTIONS[0]["base_url"]),
        instruction="\n- 使用方向键导航 | Use arrow keys to navigate\n- 按回车键选择 | Press Enter to select\n- 🇨🇳 推荐使用阿里百炼 (默认选择)",
        style=questionary.Style(
            [
                ("selected", "fg:green noinherit"),
                ("highlighted", "fg:green noinherit"),
                ("pointer", "fg:green noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        logger.info("\n[red]未选择LLM提供商，退出程序... | No LLM provider selected. Exiting...[/red]")
        exit(1)

    provider_key, url = choice

    if url == "custom":
        custom_url = questionary.text(
            "请输入自定义OpenAI端点URL | Please enter custom OpenAI endpoint URL:",
            default="https://api.openai.com/v1",
            instruction="例如: https://api.openai.com/v1 或 http://localhost:8000/v1",
        ).ask()

        if not custom_url:
            logger.info("\n[red]未输入自定义URL，退出程序... | No custom URL entered. Exiting...[/red]")
            exit(1)

        url = custom_url.strip()
        os.environ["CUSTOM_OPENAI_BASE_URL"] = url

    logger.info(f"已选择LLM提供商 | Selected provider: {provider_key}\tURL: {url}")
    return provider_key, url
