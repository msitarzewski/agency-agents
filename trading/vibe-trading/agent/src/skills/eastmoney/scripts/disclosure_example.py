#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""龙虎榜 + 大宗交易 + 融资融券披露面研究示例。

运行前提：在 agent/ 目录下执行（导入根为 agent/）。无需 token。
所有请求经东方财富共享 IP 限速层节流（按源 IP 限流）。
"""

import json

from src.tools.block_trades_tool import BlockTradesTool
from src.tools.dragon_tiger_tool import DragonTigerTool
from src.tools.margin_trading_tool import MarginTradingTool


def dragon_tiger_seats(date: str, code: str) -> None:
    """打印指定个股在某交易日的龙虎榜买卖席位排名。"""
    envelope = json.loads(DragonTigerTool().execute(date=date, code=code))
    if not envelope.get("ok"):
        print(f"龙虎榜获取失败：{envelope.get('error')}")
        return
    seats = envelope["data"].get("seats", [])
    print(f"{code} {date} 龙虎榜席位（前 3）：")
    for seat in seats[:3]:
        print(f"  {seat['seat']} 净额={seat['net']} 方向={seat['side']}")


def recent_block_trades(code: str, days: int = 30) -> None:
    """打印近 N 日大宗交易的折溢价与买卖营业部。"""
    envelope = json.loads(BlockTradesTool().execute(code=code, days=days))
    if not envelope.get("ok"):
        print(f"大宗交易获取失败：{envelope.get('error')}")
        return
    records = envelope["data"].get("records", [])
    print(f"{code} 近 {days} 日大宗交易 {len(records)} 笔：")
    for rec in records[:3]:
        print(
            f"  {rec['trade_date']} 价={rec['deal_price']} "
            f"折溢价={rec['premium_ratio']} 买方={rec['buyer_seat']}"
        )


def margin_balance_trend(code: str, days: int = 30) -> None:
    """打印融资余额趋势（最新一日）。"""
    envelope = json.loads(MarginTradingTool().execute(code=code, days=days))
    if not envelope.get("ok"):
        print(f"融资融券获取失败：{envelope.get('error')}")
        return
    rows = envelope["data"].get("rows", [])
    if rows:
        latest = rows[0]
        print(
            f"{code} {latest['trade_date']} 融资余额={latest['financing_balance']} "
            f"融券余额={latest['short_balance']}"
        )


def main() -> None:
    """主流程：三路披露面交叉验证机构动向。"""
    print("===== Eastmoney 披露面研究（龙虎榜/大宗/两融） =====")
    code = "600519.SH"
    dragon_tiger_seats("2024-01-02", code)
    recent_block_trades(code, days=30)
    margin_balance_trend(code, days=30)


if __name__ == "__main__":
    main()
