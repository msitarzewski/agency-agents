"""
快速检查 MongoDB 中 analysis_tasks 集合的字段结构与示例数据。

用法（在项目根目录）：
  python scripts/validation/inspect_analysis_tasks_schema.py

脚本会：
- 读取 app.core.config.Settings 中的 Mongo 连接配置
- 打印集合统计、示例文档 Key 列表
- 按 Key 统计值类型（str/ObjectId/int/datetime/...）
- 专项检查 user_id / user 字段的真实类型与示例值
- 复现当前后端使用的查询条件并打印命中数量
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Set

# 确保项目根目录在 sys.path 中，兼容直接 python 执行
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.core.config import settings


def _tname(v: Any) -> str:
    try:
        return type(v).__name__
    except Exception:
        return str(type(v))


async def main():
    uri = settings.MONGO_URI
    dbname = settings.MONGO_DB
    print(f"Mongo URI: {uri}")
    print(f"Mongo DB : {dbname}")

    client = AsyncIOMotorClient(uri)
    db = client[dbname]
    coll = db["analysis_tasks"]

    total = await coll.count_documents({})
    print(f"\n== 集合统计 ==\n总文档数: {total}")

    # 抓取前 50 条做结构分析
    limit = 50
    docs: List[Dict[str, Any]] = []
    async for d in coll.find({}, {"_id": 1, "task_id": 1, "user_id": 1, "user": 1, "stock_code": 1, "stock_symbol": 1, "status": 1, "progress": 1, "created_at": 1, "started_at": 1, "completed_at": 1, "parameters": 1, "result": 1}).limit(limit):
        docs.append(d)

    print(f"采样数量: {len(docs)} (limit={limit})")

    if not docs:
        print("集合为空或没有读取到示例数据。")
        return

    # 统计 key 与类型
    keys: Set[str] = set()
    types_by_key: Dict[str, Set[str]] = defaultdict(set)
    for d in docs:
        for k, v in d.items():
            keys.add(k)
            types_by_key[k].add(_tname(v))

    print("\n== 采样文档的 Key 列表 ==")
    print(", ".join(sorted(keys)))

    print("\n== 各字段的示例类型 ==")
    for k in sorted(types_by_key):
        print(f"- {k}: {sorted(types_by_key[k])}")

    # 打印几个示例文档
    print("\n== 示例文档（前3条，裁剪显示） ==")
    for d in docs[:3]:
        preview = {k: d.get(k) for k in ["_id", "task_id", "user_id", "user", "stock_code", "stock_symbol", "status", "progress", "created_at", "started_at", "completed_at"]}
        print(json.dumps(preview, default=str, ensure_ascii=False, indent=2))

    # 专项：user_id / user 字段检查
    def pick_values(field: str) -> List[Any]:
        vals: List[Any] = []
        for d in docs:
            if field in d:
                vals.append(d[field])
        return vals

    uids = pick_values("user_id")
    users = pick_values("user")
    print("\n== user_id / user 字段检查 ==")
    print(f"user_id 采样数量: {len(uids)}")
    if uids:
        print(f"user_id 示例类型: {sorted({_tname(v) for v in uids})}")
        print(f"user_id 示例值: {json.dumps([str(uids[i]) for i in range(min(3, len(uids)))], ensure_ascii=False)}")
    print(f"user    采样数量: {len(users)}")
    if users:
        print(f"user 示例类型: {sorted({_tname(v) for v in users})}")
        print(f"user 示例值: {json.dumps([str(users[i]) for i in range(min(3, len(users)))], ensure_ascii=False)}")

    # 复现后端使用的查询条件并统计命中
    admin_oid_str = "507f1f77bcf86cd799439011"
    try:
        admin_oid = ObjectId(admin_oid_str)
    except Exception:
        admin_oid = None

    cond1 = {"user_id": {"$in": ["admin", admin_oid] if admin_oid else ["admin"]}}
    cond2 = {"user": {"$in": ["admin", admin_oid] if admin_oid else ["admin"]}}
    or_cond = {"$or": [cond1, cond2]}

    c1 = await coll.count_documents(cond1)
    c2 = await coll.count_documents(cond2)
    c_or = await coll.count_documents(or_cond)

    print("\n== 查询条件命中统计 ==")
    print(f"cond1 user_id IN ['admin', ObjectId(admin)]  命中: {c1}")
    print(f"cond2 user    IN ['admin', ObjectId(admin)]  命中: {c2}")
    print(f"OR 条件合计命中: {c_or}")

    # 放宽：user_id 为字符串 admin_oid_str 的情况
    cond1b = {"user_id": {"$in": [admin_oid_str]}}
    cond2b = {"user": {"$in": [admin_oid_str]}}
    c1b = await coll.count_documents(cond1b)
    c2b = await coll.count_documents(cond2b)
    print(f"user_id == '{admin_oid_str}' 命中: {c1b}")
    print(f"user    == '{admin_oid_str}' 命中: {c2b}")

    # 全量兜底（最多展示10条 task_id）
    print("\n== 全量兜底（前10条 task_id） ==")
    ids: List[str] = []
    async for d in coll.find({}, {"task_id": 1}).limit(10):
        if d.get("task_id"):
            ids.append(d["task_id"])
    print(ids)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())

