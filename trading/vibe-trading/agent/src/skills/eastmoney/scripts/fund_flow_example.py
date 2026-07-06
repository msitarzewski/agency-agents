#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资金流向 + 板块联动研究示例。

运行前提：在 agent/ 目录下执行（导入根为 agent/）。无需 token，
所有请求经东方财富共享 IP 限速层节流。
"""

import json

from src.tools.fund_flow_tool import FundFlowTool
from src.tools.sector_tool import SectorInfoTool


def study_main_force(code: str, days: int = 30) -> dict | None:
    """读取一只股票近 N 日的主力净流入序列。

    Args:
        code: 带后缀 symbol，如 "600519.SH"。
        days: 保留最近 N 根日线。

    Returns:
        该 symbol 的资金流向结果 dict，失败返回 None。
    """
    envelope = json.loads(
        FundFlowTool().execute(codes=[code], period="daily", days=days)
    )
    if not envelope.get("ok"):
        print(f"资金流向获取失败：{envelope.get('error')}")
        return None
    result = envelope["data"].get(code)
    rows = result.get("rows", []) if result else []
    print(f"{code} 近 {len(rows)} 日资金流向（最后一行）：{rows[-1] if rows else '无'}")
    return result


def study_sectors(code: str) -> None:
    """列出该股票所属行业/概念板块，并打印今日行业涨幅榜前 5。"""
    membership = json.loads(SectorInfoTool().execute(code=code))
    if membership.get("ok"):
        boards = membership["data"].get("boards", [])
        print(f"{code} 所属板块：{[b['board_name'] for b in boards]}")

    ranking = json.loads(SectorInfoTool().execute(mode="ranking", limit=5))
    if ranking.get("ok"):
        for board in ranking["data"]["boards"]:
            print(f"  {board['board_name']}: {board['change_pct']}%")


def main() -> None:
    """主流程：资金流向 + 板块联动。"""
    print("===== Eastmoney 资金流向 + 板块研究 =====")
    code = "600519.SH"
    study_main_force(code, days=30)
    study_sectors(code)


if __name__ == "__main__":
    main()
