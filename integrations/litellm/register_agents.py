#!/usr/bin/env python3
"""
Register all xct-agents into a running LiteLLM instance via the /v1/agents API.

This script implements Approach B (full A2A integration). Each agent is
registered as a LiteLLM agent pointing to the XCT Agent Gateway service.

Requires:
  - LiteLLM proxy running with an admin API key
  - XCT Agent Gateway running (see gateway/)

Usage:
    python register_agents.py \\
        --litellm-base http://localhost:4000 \\
        --admin-key sk-your-admin-key \\
        --gateway-base http://localhost:9000 \\
        [--dry-run] [--category engineering] [--limit 10]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent.parent
AGENT_DIRS = [
    "academic", "design", "engineering", "finance", "game-development",
    "marketing", "paid-media", "product", "project-management",
    "sales", "spatial-computing", "specialized", "strategy", "support", "testing",
]


def slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def parse_agent_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    if not fm or "name" not in fm:
        return None
    body = text[end + 3:].strip()
    return {
        "name": fm.get("name", ""),
        "description": fm.get("description", ""),
        "emoji": fm.get("emoji", ""),
        "vibe": fm.get("vibe", ""),
        "system_prompt": body,
        "slug": slugify(fm.get("name", path.stem)),
        "category": path.parent.name,
    }


def collect_agents(category: str | None = None) -> list[dict]:
    agents = []
    for cat in AGENT_DIRS:
        if category and cat != category:
            continue
        cat_dir = REPO_ROOT / cat
        if not cat_dir.exists():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            agent = parse_agent_file(md_file)
            if agent:
                agents.append(agent)
    return agents


def build_agent_payload(agent: dict, gateway_base: str) -> dict:
    label = f"{agent['emoji']} {agent['name']}" if agent["emoji"] else agent["name"]
    slug = agent["slug"]
    return {
        "agent_name": f"xct-{slug}",
        "agent_card_params": {
            "protocolVersion": "1.0",
            "name": label,
            "description": agent["description"] or agent["vibe"] or agent["name"],
            "url": f"{gateway_base.rstrip('/')}/agents/{slug}/",
            "version": "1.0.0",
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {"streaming": False},
            "skills": [
                {
                    "id": slug,
                    "name": agent["name"],
                    "description": agent["description"] or agent["vibe"] or agent["name"],
                    "tags": [agent["category"]],
                    "examples": [],
                }
            ],
        },
        "litellm_params": {"make_public": True},
    }


def get_existing_agent_names(base: str, key: str) -> set[str]:
    resp = requests.get(
        f"{base}/v1/agents",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    if not resp.ok:
        return set()
    data = resp.json()
    agents = data.get("data", data) if isinstance(data, dict) else data
    return {a.get("agent_name", "") for a in (agents or [])}


def register_agent(base: str, key: str, payload: dict, existing: set[str]) -> str:
    name = payload["agent_name"]
    if name in existing:
        return "skipped (already exists)"
    resp = requests.post(
        f"{base}/v1/agents",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.ok:
        return "created"
    return f"error {resp.status_code}: {resp.text[:120]}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--litellm-base", default="http://localhost:4000")
    parser.add_argument("--admin-key", default="sk-1234")
    parser.add_argument("--gateway-base", default="http://localhost:9000")
    parser.add_argument("--category", help="Only register agents from this category")
    parser.add_argument("--limit", type=int, help="Max agents to register (for testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print payloads without making API calls")
    args = parser.parse_args()

    agents = collect_agents(args.category)
    if args.limit:
        agents = agents[: args.limit]

    print(f"Found {len(agents)} agents to register.")

    if args.dry_run:
        for a in agents[:3]:
            payload = build_agent_payload(a, args.gateway_base)
            print(yaml.dump(payload, allow_unicode=True))
        if len(agents) > 3:
            print(f"... and {len(agents) - 3} more")
        return

    existing = get_existing_agent_names(args.litellm_base, args.admin_key)
    print(f"Found {len(existing)} existing agents in LiteLLM.")

    created = skipped = errors = 0
    for agent in agents:
        payload = build_agent_payload(agent, args.gateway_base)
        result = register_agent(args.litellm_base, args.admin_key, payload, existing)
        status_icon = "✓" if result == "created" else ("→" if result.startswith("skipped") else "✗")
        print(f"  {status_icon} {payload['agent_name']}: {result}")
        if result == "created":
            created += 1
        elif result.startswith("skipped"):
            skipped += 1
        else:
            errors += 1

    print(f"\nDone — created: {created}, skipped: {skipped}, errors: {errors}")
    if created > 0:
        print(f"\nCall agents via LiteLLM:")
        print(f'  POST {args.litellm_base}/v1/chat/completions')
        print(f'  {{"model": "a2a/xct-frontend-developer", "messages": [...]}}')


if __name__ == "__main__":
    main()
