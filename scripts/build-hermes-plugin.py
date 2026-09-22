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

import bisect
import json
import math
import re
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).parent / "data" / "agents.json"
_AGENTS: list[dict[str, Any]] | None = None
_INDEX: dict[str, dict[str, Any]] | None = None
_IDF: dict[str, float] = {}
_IDF_DEFAULT = 1.0
_VOCAB: list[str] = []

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+.#_-]*", re.I)
_MAX_LIFECYCLE_CONTEXT_CHARS = 32_000
_DELEGATION_WAIT_SECONDS = 330
_CANCELLATION_WAIT_SECONDS = 30
_TRUNCATION_MARKER = (
    "\n\n[Specialist instructions truncated to fit the Hermes lifecycle context limit.]"
)

# Only the head of a body is indexed: past this point a term is usually an
# aside, not what the agent is for.
_BODY_HEAD_CHARS = 8000

# Which field a term lands in is most of the signal. A term in the name means
# the agent is about that thing; the same term 6000 characters into the body
# usually means it came up once. Weights and the two constants below were
# picked by running scripts/test-hermes-search.py over the real roster.
_FIELD_WEIGHT = {"name": 8.0, "description": 4.5, "division": 2.0, "vibe": 1.5}
_BODY_WEIGHT = 1.0
_PHRASE_BONUS = 8.0

# Matching more of the query beats spiking on one term, but not so strongly
# that a broad weak match outranks the agent the query is named after.
_COVERAGE_FLOOR = 0.6

# Query terms this long also match index terms they prefix, so "postgres"
# reaches "postgresql" and "accessib" reaches "accessibility".
_PREFIX_MIN = 5

# Below this a result is noise rather than a weak answer.
_MIN_SCORE = 1.5

# Query words that say nothing about which specialist is wanted. Searches
# arrive as questions ("who can help me review my api"), so most of a query is
# usually this list; scoring these like real terms drowns out the one word that
# decides the answer.
_STOPWORDS = frozenset("""
a about all also am an and any are as at be been being but by can cant could
did do does doing done for from get give got had has have having help how i if
im in into is it its just like make me my need needs no not of on one only or
our out over please should so some than that the their them then there these
they this those to up us use used using want was way we well what when where
which who why will with would you your
""".split())


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


def _build_index() -> dict[str, dict[str, Any]]:
    """Tokenize every agent once, per field, and count how many agents use each
    term.

    Whole tokens, not substrings. The earlier scorer asked `token in name`,
    which made "go" a hit on Godot Multiplayer Engineer, "ai" a hit on Email
    Marketing Strategist, and the letter "r" a hit on 253 of 279 names.
    """
    global _INDEX, _IDF, _IDF_DEFAULT, _VOCAB
    if _INDEX is not None:
        return _INDEX
    agents = _load_agents()
    index: dict[str, dict[str, Any]] = {}
    doc_freq: dict[str, int] = {}
    for agent in agents:
        fields = {
            "name": _tokens(agent.get("name", "")),
            "description": _tokens(agent.get("description", "")),
            "division": _tokens(agent.get("division", "")),
            "vibe": _tokens(agent.get("vibe", "")),
        }
        body = _tokens(agent.get("body", "")[:_BODY_HEAD_CHARS])
        text = "\n".join([
            agent.get("name", ""),
            agent.get("description", ""),
            agent.get("division", ""),
            agent.get("vibe", ""),
            agent.get("body", "")[:_BODY_HEAD_CHARS],
        ]).lower()
        index[agent["slug"]] = {"fields": fields, "body": body, "text": text}
        for term in body.union(*fields.values()):
            doc_freq[term] = doc_freq.get(term, 0) + 1
    total = max(len(agents), 1)
    _IDF = {term: math.log(1.0 + total / count) for term, count in doc_freq.items()}
    _IDF_DEFAULT = math.log(1.0 + total)
    _VOCAB = sorted(doc_freq)
    _INDEX = index
    return _INDEX


def _query_terms(query: str) -> set[str]:
    """The words in a query that say something about which specialist is wanted."""
    terms = _tokens(query)
    meaningful = terms - _STOPWORDS
    # A query made entirely of stop words still deserves its best effort.
    return meaningful or terms


def _expansions(term: str) -> set[str]:
    """Index terms a query term is allowed to match.

    Plain plural/singular pairs plus prefixes, so "emails" reaches the Email
    Marketing Strategist and "postgres" reaches an agent that says PostgreSQL.
    """
    forms = {term}
    if len(term) > 3:
        if term.endswith("ies"):
            forms.add(term[:-3] + "y")
        if term.endswith("es"):
            forms.add(term[:-2])
        if term.endswith("s"):
            forms.add(term[:-1])
        forms.add(term + "s")
    matches = {form for form in forms if form in _IDF}
    if len(term) >= _PREFIX_MIN:
        # _VOCAB is sorted, so every term with this prefix is one contiguous run.
        for candidate in _VOCAB[bisect.bisect_left(_VOCAB, term):]:
            if not candidate.startswith(term):
                break
            matches.add(candidate)
    return matches or {term}


def _score(agent: dict[str, Any], query_terms: dict[str, set[str]], query_text: str) -> float:
    entry = _build_index().get(agent.get("slug", ""))
    if entry is None or not query_terms:
        return 0.0
    fields = entry["fields"]
    score = 0.0
    matched = 0
    titled = 0  # matched somewhere other than the body
    for candidates in query_terms.values():
        weight = 0.0
        for field, field_weight in _FIELD_WEIGHT.items():
            if fields[field] & candidates and field_weight > weight:
                weight = field_weight
        hits = candidates & entry["body"]
        for field_tokens in fields.values():
            hits |= candidates & field_tokens
        if not hits:
            continue
        if weight:
            titled += 1
        else:
            weight = _BODY_WEIGHT
        matched += 1
        score += weight * max(_IDF.get(hit, _IDF_DEFAULT) for hit in hits)
    if not matched:
        return 0.0
    if query_text and query_text in entry["text"]:
        score += _PHRASE_BONUS
    # Covering more of the query beats spiking on a single term.
    score *= _COVERAGE_FLOOR + (1.0 - _COVERAGE_FLOOR) * matched / len(query_terms)
    if score < _MIN_SCORE:
        return 0.0
    # One common word somewhere in an 8000-character body is not a reason to
    # return an agent. Without this every roster entry matched every query.
    if not titled and matched == 1 and len(query_terms) > 2:
        return 0.0
    return score


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


def _lifecycle_context(agent: dict[str, Any]) -> str:
    context = _specialist_prompt(agent)
    if len(context) <= _MAX_LIFECYCLE_CONTEXT_CHARS:
        return context
    keep = _MAX_LIFECYCLE_CONTEXT_CHARS - len(_TRUNCATION_MARKER)
    return context[:keep] + _TRUNCATION_MARKER


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


SEARCH_DESCRIPTION = (
    "Search The Agency's on-disk specialist agent roster without loading all "
    "agents into the prompt. Use this when the user asks for an Agency/Data "
    "Swami specialist, role, discipline, or wants help choosing the right agent."
)
SEARCH_SCHEMA = {
    "name": "agency_agents_search",
    "description": SEARCH_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural-language search query."},
            "division": {"type": "string", "description": "Optional division filter, e.g. engineering, marketing, testing."},
            "limit": {"type": "integer", "description": "Maximum results, default 8, max 25."},
        },
        "required": ["query"],
    },
}

READ_DESCRIPTION = (
    "Read one Agency specialist by slug or name. Returns metadata by default "
    "and includes the full specialist instructions only when include_body is true."
)
READ_SCHEMA = {
    "name": "agency_agents_inspect",
    "description": READ_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "description": "Agent slug or exact display name."},
            "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
            "include_body": {"type": "boolean", "description": "Include full specialist instructions."},
        },
        "required": [],
    },
}

PROMPT_DESCRIPTION = (
    "Load a selected Agency specialist as a prompt block for the current task. "
    "Use after agency_agents_search when you need one specialist's full context."
)
PROMPT_SCHEMA = {
    "name": "agency_agents_load",
    "description": PROMPT_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "description": "Agent slug or exact display name."},
            "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
            "task": {"type": "string", "description": "The user's task to pair with the specialist context."},
        },
        "required": [],
    },
}

DELEGATE_DESCRIPTION = (
    "Delegate a task to one selected Agency specialist through Hermes' "
    "public subagent lifecycle. Falls back to returning the composed specialist "
    "prompt if delegation is unavailable."
)
DELEGATE_SCHEMA = {
    "name": "agency_agents_delegate",
    "description": DELEGATE_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "description": "Agent slug or exact display name."},
            "slug": {"type": "string", "description": "Alias for agent. Pass the slug from agency_agents_search results."},
            "task": {"type": "string", "description": "Concrete task for the specialist."},
        },
        "required": ["task"],
    },
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
        _build_index()
        q_terms = {term: _expansions(term) for term in _query_terms(query)}
        q_text = query.lower()
        matches: list[tuple[float, dict[str, Any]]] = []
        for agent in _load_agents():
            if division and agent.get("division", "").lower() != division:
                continue
            score = _score(agent, q_terms, q_text)
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
        fallback_prompt = _specialist_prompt(agent, task)
        handle = None
        try:
            from agent.subagent_lifecycle import SubagentLaunchRequest

            lifecycle = ctx.subagent_lifecycle
            handle = lifecycle.launch(SubagentLaunchRequest(
                goal=task,
                context=_lifecycle_context(agent),
            ))
            terminal = lifecycle.wait(
                handle, timeout_seconds=_DELEGATION_WAIT_SECONDS
            )
            if terminal.timed_out:
                try:
                    lifecycle.cancel(
                        handle,
                        reason="Agency delegation exceeded the plugin wait limit.",
                    )
                    terminal = lifecycle.wait(
                        handle, timeout_seconds=_CANCELLATION_WAIT_SECONDS
                    )
                except Exception as exc:
                    return _json({
                        "success": True,
                        "agent": _summary(agent),
                        "delegated": True,
                        "pending": True,
                        "subagent_id": handle.subagent_id,
                        "warning": f"subagent cancellation could not be confirmed: {exc}",
                    })
                if not terminal.completed:
                    return _json({
                        "success": True,
                        "agent": _summary(agent),
                        "delegated": True,
                        "pending": True,
                        "subagent_id": handle.subagent_id,
                        "state": terminal.state.value,
                        "warning": "subagent cancellation was requested but is not terminal",
                    })
            result = lifecycle.result(handle)
            if not result.ready or result.terminal_state.value != "SUCCEEDED":
                detail = (
                    result.error_message
                    or result.error_classification
                    or result.terminal_state.value
                )
                return _json({
                    "success": True,
                    "agent": _summary(agent),
                    "delegated": False,
                    "warning": f"subagent delegation failed: {detail}",
                    "prompt": fallback_prompt,
                })
            return _json({
                "success": True,
                "agent": _summary(agent),
                "delegated": True,
                "subagent_id": handle.subagent_id,
                "result": result.summary,
                "structured_result": result.structured_payload,
            })
        except Exception as exc:  # pragma: no cover - depends on Hermes runtime
            if handle is not None:
                return _json({
                    "success": True,
                    "agent": _summary(agent),
                    "delegated": True,
                    "pending": True,
                    "subagent_id": handle.subagent_id,
                    "warning": f"subagent state could not be confirmed: {exc}",
                })
            return _json({
                "success": True,
                "agent": _summary(agent),
                "delegated": False,
                "warning": f"subagent delegation unavailable: {exc}",
                "prompt": fallback_prompt,
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
        of adding hundreds of generated skills to `skills.external_dirs`. Hermes sees a
        small fixed tool surface at startup, while the complete Agency roster is
        stored on disk in `data/agents.json` and searched/loaded lazily.

        Generated agent count: {agent_count}

        ## Tools exposed to Hermes

        - `agency_agents_search` — find matching specialists by query/division.
        - `agency_agents_inspect` — inspect one specialist's metadata or full body.
        - `agency_agents_load` — compose one specialist prompt for the current task.
        - `agency_agents_delegate` — delegate through Hermes' public subagent lifecycle.

        Each tool is registered with Hermes' complete function-tool schema, including
        its name, description, and JSON `parameters`. The available arguments are:

        | Tool | Arguments |
        | --- | --- |
        | `agency_agents_search` | `query` (required), optional `division` and `limit` |
        | `agency_agents_inspect` | `agent` or `slug`, optional `include_body` |
        | `agency_agents_load` | `agent` or `slug`, optional `task` |
        | `agency_agents_delegate` | `agent` or `slug`, `task` (required) |

        A normal flow is: search by capability, take a returned `slug`, then inspect,
        load, or delegate to that specialist. You can ask Hermes to do this in natural
        language; direct tool calls are not required.

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

        Restart Hermes or start a new session after installing so the plugin and its
        tool schemas are loaded. If Hermes displays these tools without their documented
        arguments, regenerate and reinstall the plugin from the latest Agency Agents
        checkout, then restart Hermes.
        """
    ).lstrip()


def build(repo_root: Path, out_dir: Path) -> int:
    agents = collect_agents(repo_root)
    plugin_dir = out_dir / PLUGIN_NAME
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)
    (plugin_dir / "data").mkdir(parents=True, exist_ok=True)
    # newline="\n" everywhere: without it Python rewrites \n as \r\n on Windows,
    # and running convert.sh there turns the tracked integrations/hermes/README.md
    # into a CRLF diff (.gitattributes keeps this tree on LF).
    (plugin_dir / "plugin.yaml").write_text(plugin_yaml(), encoding="utf-8", newline="\n")
    (plugin_dir / "__init__.py").write_text(init_py(), encoding="utf-8", newline="\n")
    (plugin_dir / "data" / "agents.json").write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "README.md").write_text(readme(len(agents)), encoding="utf-8", newline="\n")
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
