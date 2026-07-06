"""
直接拉取 AiHubMix Models API，分析模型命名与归类情况。

用途：
1. 排查国内模型（Qwen/GLM/DeepSeek/Kimi/豆包/MiniMax）为什么在前端筛选不到；
2. 观察 AiHubMix 返回的原始 model_id 真实格式；
3. 验证当前“按模型厂家筛选”的推断规则是否覆盖不足。

运行示例：
    .\.venv\Scripts\python.exe scripts\debug\inspect_aihubmix_models.py
    .\.venv\Scripts\python.exe scripts\debug\inspect_aihubmix_models.py --providers qwen glm deepseek
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_URL = "https://aihubmix.com/api/v1/models"


def is_valid_api_key(value: str | None) -> bool:
    if not value:
        return False
    value = value.strip()
    if not value or "..." in value:
        return False
    if value.startswith("your_") or value.startswith("your-") or value.endswith("_here"):
        return False
    return len(value) > 10


def load_api_key_from_mongo() -> str | None:
    try:
        from pymongo import MongoClient
    except Exception:
        return None

    mongo_uri = os.getenv("MONGODB_CONNECTION_STRING")
    db_name = os.getenv("MONGODB_DATABASE_NAME") or os.getenv("MONGODB_DATABASE") or "tradingagentscn"
    if not mongo_uri:
        return None

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    provider = client[db_name]["llm_providers"].find_one({"name": "aihubmix"})
    if not provider:
        return None

    api_key = provider.get("api_key")
    return api_key if is_valid_api_key(api_key) else None


def infer_vendor(model_id: str) -> str:
    model_id = str(model_id or "").strip().lower()
    provider_prefix_map = [
        (("gpt-", "o1", "o3", "o4", "chatgpt-"), "openai"),
        (("claude-",), "anthropic"),
        (("gemini",), "google"),
        (("deepseek-", "deepseek"), "deepseek"),
        (("qwen-", "qwen", "tongyi"), "qwen"),
        (("glm-", "glm", "chatglm", "zhipu"), "glm"),
        (("kimi-", "kimi", "moonshot"), "kimi"),
        (("doubao-", "doubao", "seedance", "seedream"), "doubao"),
        (("minimax-", "minimax", "abab", "mimo-"), "minimax"),
        (("mistral-", "mistral"), "mistral"),
        (("meta/", "meta-", "llama-"), "meta"),
        (("jina-", "jina/"), "jina"),
        (("ernie-", "ernie", "baidu"), "baidu"),
        (("step-",), "stepfun"),
        (("hunyuan-", "hunyuan"), "hunyuan"),
    ]
    for prefixes, provider in provider_prefix_map:
        if model_id.startswith(prefixes):
            return provider
    return "other"


def fetch_models(api_url: str, api_key: str | None) -> list[dict[str, Any]]:
    headers: dict[str, str] = {}
    if is_valid_api_key(api_key):
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(
        api_url,
        params={"type": "llm", "sort_by": "order", "sort_order": "asc"},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", [])
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected payload format: {json.dumps(payload)[:500]}")
    return data


def summarize(models: list[dict[str, Any]], focus_providers: list[str], sample_limit: int) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with_tools = 0
    with_function_calling = 0

    for item in models:
        model_id = str(item.get("model_id") or item.get("id") or "").strip()
        vendor = infer_vendor(model_id)
        grouped[vendor].append(item)

        features = {part.strip().lower() for part in str(item.get("features") or "").split(",") if part.strip()}
        if "tools" in features:
            with_tools += 1
        if "function_calling" in features:
            with_function_calling += 1

    summary: dict[str, Any] = {
        "total": len(models),
        "with_tools": with_tools,
        "with_function_calling": with_function_calling,
        "group_counts": {vendor: len(items) for vendor, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))},
        "focus_samples": {},
        "other_samples": [str(item.get("model_id") or item.get("id") or "") for item in grouped.get("other", [])[:sample_limit]],
    }

    for provider in focus_providers:
        items = grouped.get(provider, [])
        summary["focus_samples"][provider] = {
            "count": len(items),
            "samples": [str(item.get("model_id") or item.get("id") or "") for item in items[:sample_limit]],
        }

    # 额外给出“看起来像国内模型但没识别出来”的可疑条目
    suspicious_patterns = re.compile(r"(qwen|glm|deepseek|kimi|moonshot|doubao|minimax|mimo|step|ernie|hunyuan)", re.I)
    summary["suspicious_other"] = [
        str(item.get("model_id") or item.get("id") or "")
        for item in grouped.get("other", [])
        if suspicious_patterns.search(str(item.get("model_id") or item.get("id") or ""))
    ][:sample_limit]

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect AiHubMix raw model list and vendor inference.")
    parser.add_argument("--api-url", default=DEFAULT_URL, help="AiHubMix Models API URL")
    parser.add_argument("--api-key", default=None, help="AiHubMix API key, overrides env and MongoDB config")
    parser.add_argument(
        "--providers",
        nargs="*",
        default=["qwen", "glm", "deepseek", "kimi", "doubao", "minimax", "google", "openai", "anthropic"],
        help="Providers to focus on in the summary",
    )
    parser.add_argument("--sample-limit", type=int, default=15, help="Sample model IDs to print for each group")
    parser.add_argument("--dump-json", default=None, help="Optional path to dump raw JSON response")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = args.api_key or os.getenv("AIHUBMIX_API_KEY") or load_api_key_from_mongo()

    print("=== AiHubMix Models API Inspect ===")
    print(f"API URL: {args.api_url}")
    print(f"API Key Source: {'provided/env/mongo' if is_valid_api_key(api_key) else 'none (try anonymous)'}")

    models = fetch_models(args.api_url, api_key)
    print(f"Fetched models: {len(models)}")

    if args.dump_json:
        dump_path = Path(args.dump_json)
        dump_path.write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Raw JSON dumped to: {dump_path}")

    summary = summarize(models, [p.lower() for p in args.providers], args.sample_limit)

    print("\n=== Group Counts ===")
    for vendor, count in summary["group_counts"].items():
        print(f"{vendor:>12}: {count}")

    print("\n=== Focus Providers ===")
    for provider, info in summary["focus_samples"].items():
        print(f"\n[{provider}] count={info['count']}")
        for item in info["samples"]:
            print(f"  - {item}")

    print("\n=== Other Samples ===")
    for item in summary["other_samples"]:
        print(f"  - {item}")

    if summary["suspicious_other"]:
        print("\n=== Suspicious Other (domestic-like but unmatched) ===")
        for item in summary["suspicious_other"]:
            print(f"  - {item}")

    print("\n=== Feature Summary ===")
    print(f"with tools: {summary['with_tools']}")
    print(f"with function_calling: {summary['with_function_calling']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
