#!/usr/bin/env python3
"""
初始化 MongoDB 索引脚本
- stock_basic_info: 为选股与查询优化字段建立索引
- sync_status: 为后台任务状态查询建立索引

用法：
  python scripts/setup/init_mongodb_indexes.py
或设置环境：
  MONGODB_HOST / MONGODB_PORT / MONGODB_DATABASE / MONGODB_USERNAME / MONGODB_PASSWORD / MONGODB_AUTH_SOURCE

注意：此脚本仅创建索引，不会删除已有索引。
"""
from __future__ import annotations

import os
from pymongo import MongoClient, ASCENDING, DESCENDING


def build_mongo_uri() -> str:
    host = os.getenv("MONGODB_HOST", "localhost")
    port = int(os.getenv("MONGODB_PORT", "27017"))
    db = os.getenv("MONGODB_DATABASE", "tradingagents")
    user = os.getenv("MONGODB_USERNAME", "")
    pwd = os.getenv("MONGODB_PASSWORD", "")
    auth_src = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    if user and pwd:
        return f"mongodb://{user}:{pwd}@{host}:{port}/{db}?authSource={auth_src}"
    return f"mongodb://{host}:{port}/{db}"


def ensure_indexes():
    uri = build_mongo_uri()
    client = MongoClient(uri)
    dbname = os.getenv("MONGODB_DATABASE", "tradingagents")
    db = client[dbname]

    # 1) stock_basic_info 索引
    sbi = db["stock_basic_info"]

    # 🔥 联合唯一键：(code, source) - 允许同一股票有多个数据源
    try:
        # 先尝试删除旧的 code 唯一索引（如果存在）
        sbi.drop_index("uniq_code")
        print("✅ 已删除旧的 code 唯一索引")
    except Exception as e:
        print(f"⚠️ 删除 uniq_code 索引失败（可能不存在）: {e}")

    try:
        # 🔥 删除旧的 full_symbol 唯一索引（如果存在）
        sbi.drop_index("full_symbol_1_unique")
        print("✅ 已删除旧的 full_symbol 唯一索引")
    except Exception as e:
        print(f"⚠️ 删除 full_symbol_1_unique 索引失败（可能不存在）: {e}")

    # 创建新的联合唯一索引
    sbi.create_index([("code", ASCENDING), ("source", ASCENDING)], unique=True, name="uniq_code_source")
    print("✅ 创建联合唯一索引: (code, source)")

    # 常用查询字段
    sbi.create_index([("code", ASCENDING)], name="idx_code")  # 🔥 非唯一索引，用于查询所有数据源
    sbi.create_index([("source", ASCENDING)], name="idx_source")  # 🔥 数据源索引
    sbi.create_index([("name", ASCENDING)], name="idx_name")
    sbi.create_index([("industry", ASCENDING)], name="idx_industry")
    sbi.create_index([("market", ASCENDING)], name="idx_market")
    sbi.create_index([("sse", ASCENDING)], name="idx_sse")
    sbi.create_index([("sec", ASCENDING)], name="idx_sec")
    # 市值与更新时间（便于排序/筛选）
    sbi.create_index([("total_mv", DESCENDING)], name="idx_total_mv_desc")
    sbi.create_index([("circ_mv", DESCENDING)], name="idx_circ_mv_desc")
    sbi.create_index([("updated_at", DESCENDING)], name="idx_updated_at_desc")
    # 财务指标索引（便于筛选）
    sbi.create_index([("pe", ASCENDING)], name="idx_pe")
    sbi.create_index([("pb", ASCENDING)], name="idx_pb")
    sbi.create_index([("turnover_rate", DESCENDING)], name="idx_turnover_rate_desc")

    # 2) sync_status 索引
    ss = db["sync_status"]
    ss.create_index([("job", ASCENDING)], unique=True, name="uniq_job")
    ss.create_index([("status", ASCENDING)], name="idx_status")
    ss.create_index([("finished_at", DESCENDING)], name="idx_finished_at_desc")

    print("✅ 索引初始化完成")


if __name__ == "__main__":
    ensure_indexes()
    print("🎉 完成")

