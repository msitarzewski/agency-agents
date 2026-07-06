#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
扫描并清理配置相关集合中的敏感字段（默认 dry-run）。
- 目标集合：system_configs、llm_providers
- 敏感字段：api_key、api_secret、password（以及可能的 variants）
- 默认仅打印变更计划；传入 --apply 方才执行更新。

使用方法（PowerShell 示例）：
  .\.venv\Scripts\python scripts\config\cleanup_sensitive_in_db.py --mongo "mongodb://localhost:27017/tradingagents" --apply
或仅查看（dry-run）：
  .\.venv\Scripts\python scripts\config\cleanup_sensitive_in_db.py --mongo "mongodb://localhost:27017/tradingagents"
"""

import argparse
import sys
import os
from typing import Any, Dict

try:
    from pymongo import MongoClient
except Exception as e:
    print("需要安装 pymongo：pip install pymongo")
    sys.exit(1)

SENSITIVE_KEYS = {"api_key", "api_secret", "password"}


def redact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    nd = {}
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            nd[k] = redact_dict(v)
        elif isinstance(v, list):
            nd[k] = [redact_dict(x) if isinstance(x, dict) else x for x in v]
        else:
            if k in SENSITIVE_KEYS and isinstance(v, str) and v.strip():
                nd[k] = "***REDACTED***"
            else:
                nd[k] = v
    return nd


def cleanup_system_configs(db, apply: bool):
    col = db["system_configs"]
    count = 0
    for doc in col.find({}):
        orig = doc.copy()
        updated = False

        # LLM configs
        llm_configs = doc.get("llm_configs", [])
        for item in llm_configs:
            if isinstance(item, dict):
                for key in list(item.keys()):
                    if key in SENSITIVE_KEYS and item.get(key):
                        item[key] = ""
                        updated = True

        # Data source configs
        ds_configs = doc.get("data_source_configs", [])
        for item in ds_configs:
            if isinstance(item, dict):
                for key in ("api_key", "api_secret"):
                    if item.get(key):
                        item[key] = ""
                        updated = True

        # Database configs
        db_configs = doc.get("database_configs", [])
        for item in db_configs:
            if isinstance(item, dict) and item.get("password"):
                item["password"] = ""
                updated = True

        if updated:
            count += 1
            if apply:
                col.update_one({"_id": doc["_id"]}, {"$set": {
                    "llm_configs": llm_configs,
                    "data_source_configs": ds_configs,
                    "database_configs": db_configs,
                }})
                print(f"[APPLY] system_configs {_id_str(doc)}: 清理完成")
            else:
                print(f"[DRY] system_configs {_id_str(doc)} 将被清理：")
                print(f"  示例：{redact_dict(orig)} -> {redact_dict(doc)}")
    return count


def cleanup_llm_providers(db, apply: bool):
    col = db["llm_providers"]
    count = 0
    for doc in col.find({}):
        updated = False
        updates = {}
        for key in SENSITIVE_KEYS:
            if key in doc and isinstance(doc[key], str) and doc[key].strip():
                updates[key] = ""
                updated = True
        if updated:
            count += 1
            if apply:
                col.update_one({"_id": doc["_id"]}, {"$set": updates})
                print(f"[APPLY] llm_providers {_id_str(doc)}: 清理 {list(updates.keys())}")
            else:
                print(f"[DRY] llm_providers {_id_str(doc)} 将清理 {list(updates.keys())}")
    return count


def _id_str(doc: Dict[str, Any]) -> str:
    try:
        return str(doc.get("_id"))
    except Exception:
        return "<unknown>"


def main():
    parser = argparse.ArgumentParser(description="清理 DB 中的敏感字段（默认 dry-run）")
    parser.add_argument("--mongo", required=False, default=os.getenv("MONGO_URI", "mongodb://localhost:27017/tradingagents"))
    parser.add_argument("--apply", action="store_true", help="实际写回清理结果（默认仅预览）")
    args = parser.parse_args()

    client = MongoClient(args.mongo)
    db_name = args.mongo.rsplit("/", 1)[-1].split("?")[0]
    db = client[db_name]

    total = 0
    total += cleanup_system_configs(db, args.apply)
    total += cleanup_llm_providers(db, args.apply)

    print(f"完成。处理文档数：{total}，模式：{'APPLY' if args.apply else 'DRY-RUN'}")


if __name__ == "__main__":
    main()

