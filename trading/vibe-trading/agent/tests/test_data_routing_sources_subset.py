"""Guard test: data-routing SKILL.md can never drift from the loader registry.

The ``data-routing`` skill is the single ROUTER and its Source Overview table
enumerates the registered backtest data sources by name. This test parses those
names straight from the markdown and asserts they form a strict **subset** of
``backtest.loaders.registry.VALID_SOURCES`` — so the doc can never name a source
the code does not actually register (code-first invariant).
"""

from __future__ import annotations

import re
from pathlib import Path

from backtest.loaders.registry import VALID_SOURCES

# SKILL.md lives next to the loader registry under the source tree:
# agent/backtest/loaders/registry.py -> agent/src/skills/data-routing/SKILL.md
_AGENT_ROOT = Path(__file__).resolve().parents[1]
_SKILL_PATH = _AGENT_ROOT / "src" / "skills" / "data-routing" / "SKILL.md"

# A Source Overview row looks like ``| tushare | A-shares ... |``; the source name
# is the first pipe-delimited cell. We collect only rows whose first cell is a bare
# lowercase identifier (the source names), skipping the header / separator rows.
_ROW_RE = re.compile(r"^\|\s*([a-z][a-z0-9_]*)\s*\|")


def _source_names_in_skill() -> set[str]:
    """Extract the source names listed in the SKILL.md Source Overview table.

    Returns:
        The set of lowercase source identifiers named in the first column of any
        markdown table row in the skill document.

    Raises:
        AssertionError: If the SKILL.md file is missing.
    """
    assert _SKILL_PATH.exists(), f"data-routing SKILL.md not found at {_SKILL_PATH}"
    text = _SKILL_PATH.read_text(encoding="utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        match = _ROW_RE.match(line.strip())
        if match:
            names.add(match.group(1))
    return names


def test_skill_names_a_nonempty_source_set() -> None:
    """The skill must actually enumerate sources (guards a broken parse / empty doc)."""
    named = _source_names_in_skill()
    # Intersect with VALID_SOURCES so we count only genuine source rows, not stray
    # first-column identifiers from the capability table (e.g. ``tushare`` appears
    # in both, ``get_fund_flow`` does not match the lowercase-id row regex anyway).
    source_rows = named & VALID_SOURCES
    assert source_rows, "data-routing SKILL.md names no registered sources"


def test_skill_sources_are_subset_of_valid_sources() -> None:
    """Every source named in the skill must be registered in VALID_SOURCES."""
    named = _source_names_in_skill()
    # The capability table's first column holds tool names (``get_market_data`` etc.)
    # which also match the lowercase-id regex; restrict the drift check to rows that
    # look like data-source rows by excluding known tool-name prefixes.
    tool_prefixes = ("get_", "screen_", "search_", "iwencai")
    candidate_sources = {
        name for name in named if not name.startswith(tool_prefixes)
    }
    unknown = candidate_sources - VALID_SOURCES
    assert not unknown, (
        f"data-routing SKILL.md names sources absent from VALID_SOURCES: "
        f"{sorted(unknown)}"
    )


def test_new_sources_are_documented() -> None:
    """The eight newly registered sources must each appear in the Source Overview."""
    named = _source_names_in_skill()
    new_sources = {
        "eastmoney",
        "sina",
        "stooq",
        "yahoo",
        "finnhub",
        "alphavantage",
        "tiingo",
        "fmp",
    }
    missing = new_sources - named
    assert not missing, f"data-routing SKILL.md missing new source rows: {sorted(missing)}"


# A Capability table row looks like ``| Stock news | `get_stock_news` | A-share, US, HK | — |``.
# Capture the tool name (col 2, backtick-wrapped) and its market-coverage cell (col 3).
_CAPABILITY_RE = re.compile(
    r"^\|[^|]*\|\s*`([a-z_]+)`\s*\|\s*([^|]+?)\s*\|"
)

# Market tokens we assert on, mapped to the substrings each tool's live ``description``
# uses to name that market. The doc's coverage column must name every market the
# tool's own description claims to cover (doc-vs-code drift guard).
_MARKET_TOKENS = {
    "A-share": ("A-share",),
    "US": ("US",),
    "HK": ("HK", "Hong Kong"),
}


def _capability_markets_in_skill() -> dict[str, str]:
    """Extract the market-coverage cell for each Capability-table tool.

    Returns:
        Mapping of tool name -> the raw market-coverage cell text (column 3) for
        every row in the SKILL.md Capability table.
    """
    text = _SKILL_PATH.read_text(encoding="utf-8")
    coverage: dict[str, str] = {}
    for line in text.splitlines():
        match = _CAPABILITY_RE.match(line.strip())
        if match:
            coverage[match.group(1)] = match.group(2)
    return coverage


def test_capability_market_coverage_matches_tool_descriptions() -> None:
    """The Capability table must name every market each tool's description covers.

    Regression guard for B12: ``get_stock_news`` and ``get_financial_statements``
    both cover A-share/US/HK per their live tool ``description`` strings, but the
    router table previously listed only ``A-share, US`` (dropping HK). Derive the
    expected markets from the tools themselves so the doc can never under-state
    coverage again.
    """
    from src.tools.financial_statements_tool import FinancialStatementsTool
    from src.tools.stock_news_tool import StockNewsTool

    coverage = _capability_markets_in_skill()
    tools = {
        "get_stock_news": StockNewsTool.description,
        "get_financial_statements": FinancialStatementsTool.description,
    }
    for tool_name, tool_desc in tools.items():
        assert tool_name in coverage, (
            f"data-routing SKILL.md Capability table missing row for {tool_name}"
        )
        doc_cell = coverage[tool_name]
        for market, desc_aliases in _MARKET_TOKENS.items():
            covered_by_tool = any(alias in tool_desc for alias in desc_aliases)
            if not covered_by_tool:
                continue
            doc_aliases = (market,) + tuple(
                a for a in desc_aliases if a != market
            )
            assert any(alias in doc_cell for alias in doc_aliases), (
                f"{tool_name} description covers {market} but the data-routing "
                f"Capability column lists only {doc_cell!r}"
            )
