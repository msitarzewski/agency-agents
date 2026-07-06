#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研报舆情 + 美股/港股财报基本面研究示例。

运行前提：在 agent/ 目录下执行（导入根为 agent/）。无需 token。
研报/财报经东方财富（及新浪/同花顺）共享 IP 限速层节流。
"""

import json

from src.tools.financial_statements_tool import FinancialStatementsTool
from src.tools.research_reports_tool import ResearchReportsTool
from src.tools.shareholder_count_tool import ShareholderCountTool


def broker_consensus(code: str, limit: int = 10) -> None:
    """打印券商研报评级分布与一致预期 EPS。"""
    envelope = json.loads(ResearchReportsTool().execute(code=code, limit=limit))
    if not envelope.get("ok"):
        print(f"研报获取失败：{envelope.get('error')}")
        return
    data = envelope["data"]
    ratings = [r["rating"] for r in data["reports"] if r.get("rating")]
    print(f"{code} 近 {limit} 篇研报评级：{ratings}")
    print(f"  一致预期 EPS：{data.get('consensus_eps')}")


def us_hk_indicators(code: str) -> None:
    """打印美股/港股主要指标（GMAININDICATOR）的最新报告期。"""
    envelope = json.loads(
        FinancialStatementsTool().execute(
            code=code, statement="indicators", period="annual"
        )
    )
    if not envelope.get("ok"):
        print(f"财报获取失败：{envelope.get('error')}")
        return
    result = envelope["data"].get(code, {})
    periods = result.get("periods", [])
    print(f"{code} 主要指标报告期数：{len(periods)}（来源 {envelope['source']}）")


def holder_trend(code: str) -> None:
    """打印 A 股股东户数环比趋势（最新两期）。"""
    envelope = json.loads(ShareholderCountTool().execute(code=code))
    if not envelope.get("ok"):
        print(f"股东户数获取失败：{envelope.get('error')}")
        return
    for period in envelope["data"]["periods"][:2]:
        print(
            f"  {period['end_date']} 户数={period['holder_count']} "
            f"环比={period['holder_count_change_pct']}%"
        )


def main() -> None:
    """主流程：基本面 + 舆情交叉。"""
    print("===== Eastmoney 基本面 + 研报研究 =====")
    broker_consensus("600519.SH", limit=10)
    holder_trend("600519.SH")
    us_hk_indicators("AAPL.US")
    us_hk_indicators("00700.HK")


if __name__ == "__main__":
    main()
