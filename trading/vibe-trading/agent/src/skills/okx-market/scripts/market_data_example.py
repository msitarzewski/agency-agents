#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加密货币行情数据获取示例脚本。"""

from typing import Optional

import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://www.okx.com/api/v5"


def get_ticker(inst_id: str) -> Optional[dict]:
    """获取单个产品的实时行情。

    Args:
        inst_id: 交易产品ID，如 BTC-USDT。

    Returns:
        行情数据字典，失败返回 None。
    """
    try:
        resp = requests.get(f"{BASE_URL}/market/ticker", params={"instId": inst_id})
        data = resp.json()
        if data["code"] != "0":
            print(f"API错误: {data['msg']}")
            return None
        ticker = data["data"][0]
        last = float(ticker["last"])
        open24h = float(ticker["open24h"])
        chg = (last / open24h - 1) * 100
        print(f"{inst_id}  最新价: {last}  24h涨跌: {chg:+.2f}%  24h量: {ticker['vol24h']}")
        return ticker
    except Exception as e:
        print(f"获取行情失败: {e}")
        return None


def get_top_tickers(inst_type: str = "SPOT", top_n: int = 10) -> Optional[pd.DataFrame]:
    """获取成交额排名前N的交易对。

    Args:
        inst_type: 产品类型，SPOT/SWAP/FUTURES/OPTION。
        top_n: 返回前N名。

    Returns:
        DataFrame，失败返回 None。
    """
    try:
        resp = requests.get(f"{BASE_URL}/market/tickers", params={"instType": inst_type})
        tickers = resp.json()["data"]
        df = pd.DataFrame(tickers)
        df["volCcy24h"] = df["volCcy24h"].astype(float)
        df["last"] = df["last"].astype(float)
        df = df.sort_values("volCcy24h", ascending=False).head(top_n)
        print(f"\n{inst_type} 成交额 TOP {top_n}:")
        print(df[["instId", "last", "volCcy24h"]].to_string(index=False))
        return df
    except Exception as e:
        print(f"获取批量行情失败: {e}")
        return None


def get_funding_rates(symbols: Optional[list] = None) -> Optional[pd.DataFrame]:
    """获取永续合约资金费率。

    Args:
        symbols: 合约ID列表，如 ['BTC-USDT-SWAP']。默认获取主流币种。

    Returns:
        DataFrame，失败返回 None。
    """
    if symbols is None:
        symbols = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "DOGE-USDT-SWAP"]

    rows = []
    for sym in symbols:
        try:
            resp = requests.get(f"{BASE_URL}/public/funding-rate", params={"instId": sym})
            data = resp.json()["data"][0]
            rate = float(data["fundingRate"])
            annual = rate * 3 * 365 * 100
            rows.append({"instId": sym, "fundingRate": rate, "annualized": f"{annual:.2f}%"})
        except Exception as e:
            print(f"获取 {sym} 资金费率失败: {e}")

    if rows:
        df = pd.DataFrame(rows)
        print("\n永续合约资金费率:")
        print(df.to_string(index=False))
        return df
    return None


def main():
    """主函数。"""
    print("===== OKX 加密货币行情获取示例 =====\n")

    # 获取主流币种行情
    for symbol in ["BTC-USDT", "ETH-USDT", "SOL-USDT"]:
        get_ticker(symbol)

    # 获取现货成交额 TOP 10
    get_top_tickers("SPOT", 10)

    # 获取资金费率
    get_funding_rates()


if __name__ == "__main__":
    main()
