#!/usr/bin/env python3
"""
Generate xct-litellm configuration from xct-agents agent definitions.

Produces two YAML snippets:
  1. model_list entries (Approach A — simplest, works immediately)
  2. agent_list entries (Approach B — full A2A integration, requires gateway service)

Usage:
    python generate_config.py [--output model_list.yaml] [--approach model|agent|both]
                              [--model claude-3-5-sonnet-20241022]
                              [--gateway-base http://localhost:9000]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

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
    """Parse a markdown agent file and return its metadata + system prompt."""
    text = path.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None

    try:
        frontmatter = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None

    if not frontmatter or "name" not in frontmatter:
        return None

    body = text[end + 3:].strip()

    return {
        "name": frontmatter.get("name", ""),
        "description": frontmatter.get("description", ""),
        "emoji": frontmatter.get("emoji", ""),
        "vibe": frontmatter.get("vibe", ""),
        "color": frontmatter.get("color", ""),
        "tools": frontmatter.get("tools", []),
        "system_prompt": body,
        "slug": slugify(frontmatter.get("name", path.stem)),
        "category": path.parent.name,
        "source_file": str(path.relative_to(REPO_ROOT)),
    }


def collect_agents(repo_root: Path) -> list[dict]:
    agents = []
    for category in AGENT_DIRS:
        cat_dir = repo_root / category
        if not cat_dir.exists():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            agent = parse_agent_file(md_file)
            if agent:
                agents.append(agent)
    return agents


def build_model_list(agents: list[dict], base_model: str) -> list[dict]:
    """Approach A: each agent as a model_list entry with litellm_system_prompt."""
    entries = []
    for a in agents:
        label = f"{a['emoji']} {a['name']}" if a["emoji"] else a["name"]
        entries.append({
            "model_name": f"xct-{a['slug']}",
            "litellm_params": {
                "model": base_model,
                "litellm_system_prompt": a["system_prompt"],
            },
            "model_info": {
                "description": f"{label} — {a['description']}",
                "category": a["category"],
            },
        })
    return entries


def build_agent_list(agents: list[dict], gateway_base: str) -> list[dict]:
    """Approach B: each agent as an agent_list entry pointing to the gateway service."""
    entries = []
    for a in agents:
        label = f"{a['emoji']} {a['name']}" if a["emoji"] else a["name"]
        entries.append({
            "agent_name": f"xct-{a['slug']}",
            "agent_card_params": {
                "protocolVersion": "1.0",
                "name": label,
                "description": a["description"] or a["vibe"] or a["name"],
                "url": f"{gateway_base.rstrip('/')}/agents/{a['slug']}/",
                "version": "1.0.0",
                "defaultInputModes": ["text"],
                "defaultOutputModes": ["text"],
                "capabilities": {"streaming": False},
                "skills": [
                    {
                        "id": a["slug"],
                        "name": a["name"],
                        "description": a["description"] or a["vibe"],
                        "tags": [a["category"]],
                        "examples": [],
                    }
                ],
            },
            "litellm_params": {"make_public": True},
        })
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="litellm_agents.yaml",
                        help="Output file (default: litellm_agents.yaml)")
    parser.add_argument("--approach", choices=["model", "agent", "both"], default="both",
                        help="Which YAML section(s) to generate (default: both)")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022",
                        help="Base LLM model for model_list approach")
    parser.add_argument("--gateway-base", default="http://localhost:9000",
                        help="Gateway service base URL for agent_list approach")
    parser.add_argument("--category", help="Only include agents from this category")
    parser.add_argument("--limit", type=int, help="Max number of agents (for testing)")
    args = parser.parse_args()

    agents = collect_agents(REPO_ROOT)
    if args.category:
        agents = [a for a in agents if a["category"] == args.category]
    if args.limit:
        agents = agents[: args.limit]

    if not agents:
        print("No agents found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(agents)} agents from {len(set(a['category'] for a in agents))} categories.")

    output: dict = {}
    if args.approach in ("model", "both"):
        output["model_list"] = build_model_list(agents, args.model)
    if args.approach in ("agent", "both"):
        output["agent_list"] = build_agent_list(agents, args.gateway_base)

    out_path = Path(args.output)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False, width=120)

    print(f"Written to {out_path}")
    if args.approach in ("model", "both"):
        print(f"  model_list: {len(output.get('model_list', []))} entries")
        print(f"  → Add this to proxy_server_config.yaml model_list section")
        print(f"  → Call agents via: {{\"model\": \"xct-<slug>\"}} in chat/completions")
    if args.approach in ("agent", "both"):
        print(f"  agent_list: {len(output.get('agent_list', []))} entries")
        print(f"  → Start gateway: cd gateway && uvicorn main:app --port 9000")
        print(f"  → Call agents via: {{\"model\": \"a2a/xct-<slug>\"}} in chat/completions")


if __name__ == "__main__":
    main()
