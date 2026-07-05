#!/usr/bin/env python3
"""Build the Hermes lazy-router plugin for The Agency agents.

The generated plugin exposes a small fixed tool surface to Hermes and keeps the
large agent roster in an on-disk JSON data file. That avoids using
skills.external_dirs, which advertises every Agency agent in Hermes' initial
skill catalog.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from pathlib import Path

PLUGIN_NAME = "agency-agents-router"


def division_dirs(repo_root: Path) -> list[str]:
    # divisions.json (repo root) is the single source of truth for the division
    # set. Read it rather than hardcoding a copy here: a hardcoded list silently
    # drops new divisions from the Hermes roster (e.g. healthcare) the moment the
    # catalog grows. check-divisions.sh guards divisions.json against the tracked
    # dirs, so deriving from it keeps this plugin in sync by construction.
    data = json.loads((repo_root / "divisions.json").read_text(encoding="utf-8"))
    return sorted(data["divisions"].keys())


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def parse_agent(path: Path, repo_root: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return None
    frontmatter = parts[1]
    body = parts[2].lstrip("\n")
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    name = fields.get("name", "").strip()
    if not name:
        return None
    rel = path.relative_to(repo_root)
    division = rel.parts[0]
    return {
        "slug": slugify(name),
        "name": name,
        "description": fields.get("description", "").strip(),
        "division": division,
        "color": fields.get("color", "").strip(),
        "emoji": fields.get("emoji", "").strip(),
        "vibe": fields.get("vibe", "").strip(),
        "source_path": str(rel),
        "body": body,
    }


def collect_agents(repo_root: Path) -> list[dict[str, str]]:
    agents: list[dict[str, str]] = []
    for dirname in division_dirs(repo_root):
        base = repo_root / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            parsed = parse_agent(path, repo_root)
            if parsed:
                agents.append(parsed)
    agents.sort(key=lambda item: (item["division"], item["slug"]))
    seen: set[str] = set()
    duplicates: set[str] = set()
    for agent in agents:
        slug = agent["slug"]
        if slug in seen:
            duplicates.add(slug)
        seen.add(slug)
    if duplicates:
        dupes = ", ".join(sorted(duplicates))
        raise SystemExit(f"duplicate Hermes agent slugs: {dupes}")
    return agents


def plugin_yaml() -> str:
    return textwrap.dedent(
        f"""
        name: {PLUGIN_NAME}
        version: 1.0.0
        description: Lazy search/load/delegate router for The Agency agent roster.
        provides_tools:
          - agency_agents_search
          - agency_agents_inspect
          - agency_agents_load
          - agency_agents_delegate
        """
    ).lstrip()


def init_py() -> str:
    return r'''"""Hermes plugin: lazy router for The Agency agents."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).parent / "data" / "agents.json"
_AGENTS: list[dict[str, Any]] | None = None

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+.#_-]*", re.I)


def _load_agents() -> list[dict[str, Any]]:
    global _AGENTS
    if _AGENTS is None:
        _AGENTS = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return _AGENTS


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _WORD_RE.findall(text or "")}


def _agent_lookup(identifier: str) -> dict[str, Any] | None:
    needle = (identifier or "").strip().lower()
    if not needle:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", needle).strip("-")
    for agent in _load_agents():
        if agent["slug"] == slug or agent["name"].lower() == needle:
            return agent
    return None


def _identifier(args: dict[str, Any]) -> str:
    # Accept either "agent" or "slug": agency_agents_search returns results keyed
    # by "slug", so callers naturally chain search -> load/inspect/delegate with
    # slug=. Both name the same thing (a slug or exact display name).
    return str(args.get("agent") or args.get("slug") or "").strip()


def _not_found(identifier: str) -> dict[str, Any]:
    return {
        "success": False,
        "error": "agent not found" if identifier else "agent or slug is required",
        "agent": identifier or None,
    }


def _score(agent: dict[str, Any], query_tokens: set[str], query_text: str) -> float:
    haystack_fields = [
        agent.get("name", ""),
        agent.get("description", ""),
        agent.get("division", ""),
        agent.get("vibe", ""),
        agent.get("body", "")[:8000],
    ]
    haystack_text = "\n".join(haystack_fields).lower()
    haystack_tokens = _tokens(haystack_text)
    overlap = query_tokens & haystack_tokens
    score = float(len(overlap))
    if query_text and query_text in haystack_text:
        score += 5.0
    name = agent.get("name", "").lower()
    description = agent.get("description", "").lower()
    for token in query_tokens:
        if token in name:
            score += 3.0
        if token in description:
            score += 1.5
    if score == 0.0:
        return 0.0
    # Slightly prefer focused descriptions over huge bodies when scores tie.
    return score + (1.0 / math.sqrt(max(len(haystack_tokens), 1)))


def _summary(agent: dict[str, Any], score: float | None = None) -> dict[str, Any]:
    item = {
        "slug": agent["slug"],
        "name": agent["name"],
        "division": agent["division"],
        "description": agent.get("description", ""),
        "vibe": agent.get("vibe", ""),
        "source_path": agent.get("source_path", ""),
    }
    if score is not None:
        item["score"] = round(score, 3)
    return item


def _specialist_prompt(agent: dict[str, Any], task: str = "") -> str:
    task_block = f"\n\n## User task\n{task.strip()}\n" if task and task.strip() else ""
    return (
        f"Use the following Agency specialist context for this turn. "
        f"Adopt the specialist's relevant standards and checklists, but obey the "
        f"user's current request and higher-priority system/developer instructions.\n\n"
        f"# {agent['name']} ({agent['slug']})\n\n"
        f"Division: {agent.get('division', '')}\n"
        f"Description: {agent.get('description', '')}\n"
        f"Source: {agent.get('source_path', '')}\n"
        f"{task_block}\n\n"
        f"## Specialist instructions\n{agent.get('body', '')}"
    )


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


SEARCH_DESCRIPTION = (
    "Search The Agency's on-disk specialist agent roster without loading all "
    "agents into the prompt. Use this when the user asks for an Agency/Data "
    "Swami specialist, role, discipline, or wants help choosing the right agent."
)
SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Natural-language search query."},
        "division": {"type": "string", "description": "Optional division filter, e.g. engineering, marketing, testing."},
        "limit": {"type": "integer", "description": "Maximum results, default 8, max 25."},
    },
    "required": ["query"],
}

READ_DESCRIPTION = (
    "Read one Agency specialist by slug or name. Returns metadata by default "
    "and includes the full specialist instructions only when include_body is true."
)
READ_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string", "description": "Agent slug or exact display name."},
        "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
        "include_body": {"type": "boolean", "description": "Include full specialist instructions."},
    },
    "required": [],
}

PROMPT_DESCRIPTION = (
    "Load a selected Agency specialist as a prompt block for the current task. "
    "Use after agency_agents_search when you need one specialist's full context."
)
PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string", "description": "Agent slug or exact display name."},
        "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
        "task": {"type": "string", "description": "The user's task to pair with the specialist context."},
    },
    "required": [],
}

DELEGATE_DESCRIPTION = (
    "Delegate a task to one selected Agency specialist through Hermes' "
    "delegate_task tool when available. Falls back to returning the composed "
    "specialist prompt if delegation is unavailable."
)
DELEGATE_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {"type": "string", "description": "Agent slug or exact display name."},
        "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
        "task": {"type": "string", "description": "Concrete task for the specialist."},
        "toolsets": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional Hermes toolsets for the delegated worker, e.g. ['terminal','file'].",
        },
    },
    "required": ["task"],
}


def register(ctx):
    def search(args: dict[str, Any], **kwargs) -> str:
        del kwargs
        query = str(args.get("query", "")).strip()
        if not query:
            return _json({"success": False, "error": "query is required"})
        division = str(args.get("division", "")).strip().lower()
        try:
            limit = min(max(int(args.get("limit", 8)), 1), 25)
        except Exception:
            limit = 8
        q_tokens = _tokens(query)
        q_text = query.lower()
        matches: list[tuple[float, dict[str, Any]]] = []
        for agent in _load_agents():
            if division and agent.get("division", "").lower() != division:
                continue
            score = _score(agent, q_tokens, q_text)
            if score > 0:
                matches.append((score, agent))
        matches.sort(key=lambda item: (-item[0], item[1]["division"], item[1]["slug"]))
        return _json({
            "success": True,
            "query": query,
            "count": len(matches),
            "results": [_summary(agent, score) for score, agent in matches[:limit]],
        })

    def read(args: dict[str, Any], **kwargs) -> str:
        del kwargs
        identifier = _identifier(args)
        agent = _agent_lookup(identifier)
        if not agent:
            return _json(_not_found(identifier))
        payload = {"success": True, "agent": _summary(agent)}
        if bool(args.get("include_body", False)):
            payload["body"] = agent.get("body", "")
        return _json(payload)

    def prompt(args: dict[str, Any], **kwargs) -> str:
        del kwargs
        identifier = _identifier(args)
        agent = _agent_lookup(identifier)
        if not agent:
            return _json(_not_found(identifier))
        return _json({
            "success": True,
            "agent": _summary(agent),
            "prompt": _specialist_prompt(agent, str(args.get("task", ""))),
        })

    def delegate(args: dict[str, Any], **kwargs) -> str:
        del kwargs
        identifier = _identifier(args)
        agent = _agent_lookup(identifier)
        task = str(args.get("task", "")).strip()
        if not agent:
            return _json(_not_found(identifier))
        if not task:
            return _json({"success": False, "error": "task is required"})
        composed = _specialist_prompt(agent, task)
        delegate_args: dict[str, Any] = {
            "goal": task,
            "context": composed,
        }
        toolsets = args.get("toolsets")
        if isinstance(toolsets, list) and toolsets:
            delegate_args["toolsets"] = [str(item) for item in toolsets]
        try:
            result = ctx.dispatch_tool("delegate_task", delegate_args)
            return _json({"success": True, "agent": _summary(agent), "delegated": True, "result": result})
        except Exception as exc:  # pragma: no cover - depends on Hermes runtime
            return _json({
                "success": True,
                "agent": _summary(agent),
                "delegated": False,
                "warning": f"delegate_task unavailable: {exc}",
                "prompt": composed,
            })

    ctx.register_tool(
        name="agency_agents_search",
        toolset="agency_agents",
        schema=SEARCH_SCHEMA,
        handler=search,
        description=SEARCH_DESCRIPTION,
    )
    ctx.register_tool(
        name="agency_agents_inspect",
        toolset="agency_agents",
        schema=READ_SCHEMA,
        handler=read,
        description=READ_DESCRIPTION,
    )
    ctx.register_tool(
        name="agency_agents_load",
        toolset="agency_agents",
        schema=PROMPT_SCHEMA,
        handler=prompt,
        description=PROMPT_DESCRIPTION,
    )
    ctx.register_tool(
        name="agency_agents_delegate",
        toolset="agency_agents",
        schema=DELEGATE_SCHEMA,
        handler=delegate,
        description=DELEGATE_DESCRIPTION,
    )
'''


def readme(agent_count: int) -> str:
    return textwrap.dedent(
        f"""
        # Hermes Agency Agents Router Plugin

        Generated by `scripts/convert.sh --tool hermes`.

        This integration installs one Hermes plugin named `{PLUGIN_NAME}` instead
        of adding 232+ generated skills to `skills.external_dirs`. Hermes sees a
        small fixed tool surface at startup, while the complete Agency roster is
        stored on disk in `data/agents.json` and searched/loaded lazily.

        Generated agent count: {agent_count}

        ## Tools exposed to Hermes

        - `agency_agents_search` — find matching specialists by query/division.
        - `agency_agents_inspect` — inspect one specialist's metadata or full body.
        - `agency_agents_load` — compose one specialist prompt for the current task.
        - `agency_agents_delegate` — delegate through Hermes `delegate_task` when available.

        ## Specialist usage instruction for Hermes

        When a Hermes project needs Agency specialists, explicitly ask Hermes to use
        the `{PLUGIN_NAME}` plugin/router and load only the specialists needed for
        the current phase. Do not ask Hermes to install or preload the full Agency
        roster as skills.

        Recommended project instruction:

        ```text
        Use the agency-agents-router plugin. Search the Agency roster for the right
        specialists, then load or delegate only the specific agents needed for each
        part of the project. For multi-discipline projects, use multiple selected
        specialists across the project, but keep routing lazy: do not preload the
        full Agency roster and do not add agency-agents to skills.external_dirs.
        ```

        Example:

        ```text
        For this Data Swami build, use the agency-agents-router plugin to pick
        relevant Agency specialists. Search first, then delegate to selected agents
        such as frontend, backend, UX, QA, data engineering, and product strategy as
        needed. Load/delegate each specialist on demand rather than loading all
        Agency agents at startup.
        ```

        ## Install

        ```bash
        ./scripts/convert.sh --tool hermes
        ./scripts/install.sh --tool hermes
        ```

        The installer copies the generated plugin to:

        ```text
        ${{HERMES_HOME:-~/.hermes}}/plugins/{PLUGIN_NAME}
        ```

        It then enables `{PLUGIN_NAME}` under `plugins.enabled` in the Hermes
        config. It does **not** write to `skills.external_dirs`.
        """
    ).lstrip()


def build(repo_root: Path, out_dir: Path) -> int:
    agents = collect_agents(repo_root)
    plugin_dir = out_dir / PLUGIN_NAME
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)
    (plugin_dir / "data").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.yaml").write_text(plugin_yaml(), encoding="utf-8")
    (plugin_dir / "__init__.py").write_text(init_py(), encoding="utf-8")
    (plugin_dir / "data" / "agents.json").write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(readme(len(agents)), encoding="utf-8")
    return len(agents)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None, help="Output directory, default integrations/hermes")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = (args.out or (repo_root / "integrations" / "hermes")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    count = build(repo_root, out_dir)
    print(count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
