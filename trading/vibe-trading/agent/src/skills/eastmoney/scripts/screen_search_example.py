#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码搜索 + 全市场选股研究示例。

运行前提：在 agent/ 目录下执行（导入根为 agent/）。无需 token。
所有请求经东方财富共享 IP 限速层节流（按源 IP 限流）。
"""

import json

from src.tools.market_screener_tool import MarketScreenerTool
from src.tools.symbol_search_tool import SymbolSearchTool


def resolve_symbol(query: str, limit: int = 5) -> str | None:
    """把名称/片段解析为最佳候选 symbol。

    Args:
        query: 公司名或代码片段，如 "茅台" / "apple"。
        limit: 候选数上限。

    Returns:
        第一个候选 symbol，无候选返回 None。
    """
    envelope = json.loads(SymbolSearchTool().execute(query=query, limit=limit))
    candidates = envelope.get("data", {}).get("candidates", [])
    print(f"'{query}' 候选：{[c['symbol'] for c in candidates]}")
    return candidates[0]["symbol"] if candidates else None


def top_movers(market: str, top_n: int = 10) -> None:
    """打印某市场今日涨幅榜前 N。"""
    envelope = json.loads(
        MarketScreenerTool().execute(market=market, sort_by="change_pct", top_n=top_n)
    )
    if not envelope.get("ok"):
        print(f"选股失败：{envelope.get('error')}")
        return
    print(f"{market} 今日涨幅榜：")
    for row in envelope["data"][:5]:
        print(f"  {row['code']} {row['name']} {row['change_pct']}%")


def main() -> None:
    """主流程：先搜代码再看市场动向。"""
    print("===== Eastmoney 代码搜索 + 全市场选股 =====")
    symbol = resolve_symbol("贵州茅台")
    print(f"解析得到：{symbol}")
    top_movers("a", top_n=10)
    top_movers("us", top_n=10)


if __name__ == "__main__":
    main()
