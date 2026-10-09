#!/usr/bin/env python3
"""dispatcher.py — Local-First Dispatcher for Agency Agents (Python reference).

Run any agent in this repo against a LOCAL OpenAI-compatible LLM runtime
(Ollama, LM Studio, llama.cpp, vLLM, Apple MLX, etc.) at $0 inference cost.

Mirrors the Node.js dispatcher's behavior — same agent files, same shape of
return value, same flag set. Pick whichever language fits your stack.

Quick start:

    # 1. Start any OpenAI-compatible local runtime, e.g. Ollama:
    ollama serve
    ollama pull llama3.1:8b

    # 2. Dispatch an agent
    python3 dispatcher.py \\
      --agent ../../engineering/backend-architect \\
      --task "Outline a sharded Postgres schema for a multi-tenant SaaS"

    # 3. Use a different runtime by overriding base URL + model:
    python3 dispatcher.py \\
      --agent ../../design/whimsy-injector \\
      --task "3 bullets on UI delight" \\
      --base-url http://127.0.0.1:1234/v1 \\
      --model "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"

Programmatic use:

    from dispatcher import load_agent, dispatch_agent
    agent = load_agent("../../engineering/backend-architect")
    result = dispatch_agent(
        agent=agent,
        task="Sketch a CDN cache invalidation strategy",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.1:8b",
    )
    print(result["content"])

Dependencies: stdlib only (urllib, json, os). No requests/httpx required.
License: MIT (matches the repo).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ─── Agent loading ─────────────────────────────────────────────────────────

@dataclass
class Agent:
    name: str
    description: str
    body: str
    path: Path
    frontmatter: dict


_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def _resolve_agent_path(path_or_dir: str) -> Path:
    p = Path(path_or_dir).resolve()
    if p.is_dir():
        candidates = sorted(p.glob("*.md"))
        if not candidates:
            raise FileNotFoundError(f"no .md files in {p}")
        if len(candidates) > 1:
            names = ", ".join(c.name for c in candidates)
            raise ValueError(f"multiple .md files in {p}: {names} — pick one")
        return candidates[0]
    if p.exists():
        return p
    # allow `--agent foo` → `foo.md`
    with_ext = p if p.suffix == ".md" else p.with_suffix(".md")
    if with_ext.exists():
        return with_ext
    raise FileNotFoundError(f"agent file not found: {p}")


def load_agent(path_or_dir: str) -> Agent:
    """Load an agent .md file. Accepts either a direct file or a directory
    containing exactly one .md."""
    fp = _resolve_agent_path(path_or_dir)
    raw = fp.read_text(encoding="utf-8")
    fm: dict = {}
    body = raw
    m = _FRONTMATTER_RE.match(raw)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            kv = _KV_RE.match(line)
            if not kv:
                continue
            v = kv.group(2).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            fm[kv.group(1)] = v
    return Agent(
        name=fm.get("name", fp.stem),
        description=fm.get("description", ""),
        body=body.strip(),
        path=fp,
        frontmatter=fm,
    )


def list_agents(directory: str) -> list[dict]:
    """List agent files under a directory (recurses one level)."""
    d = Path(directory).resolve()
    if not d.is_dir():
        raise NotADirectoryError(f"not a directory: {d}")
    out: list[dict] = []
    for entry in sorted(d.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            try:
                a = load_agent(entry)
                out.append({"name": a.name, "description": a.description, "path": str(entry)})
            except Exception:
                continue
        elif entry.is_dir():
            for sub in sorted(entry.glob("*.md")):
                try:
                    a = load_agent(sub)
                    out.append({"name": a.name, "description": a.description, "path": str(sub)})
                except Exception:
                    continue
    return out


# ─── Dispatch ──────────────────────────────────────────────────────────────

def dispatch_agent(
    *,
    agent: Agent,
    task: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    api_key: Optional[str] = None,
    timeout_s: float = 120.0,
) -> dict:
    """Dispatch a task to a loaded agent against a local OpenAI-compatible
    runtime. Returns a dict matching the Node.js dispatcher's shape:

        { "ok": True, "agent": <name>, "content": <str>,
          "finish_reason": <str|None>, "model": <str>,
          "usage": <dict|None>, "latency_ms": <int> }

    On failure the dict has ok=False plus error/detail.
    """
    if not isinstance(agent, Agent) or not agent.body:
        return {"ok": False, "error": "agent required (from load_agent)"}
    if not isinstance(task, str) or not task.strip():
        return {"ok": False, "error": "task required (non-empty string)"}

    base_url = base_url or os.environ.get("AGENCY_BASE_URL", "http://127.0.0.1:11434/v1")
    model = model or os.environ.get("AGENCY_MODEL", "llama3.1:8b")
    api_key = api_key or os.environ.get("AGENCY_API_KEY")

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": agent.body},
            {"role": "user", "content": task},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "error": f"runtime_http_{e.code}",
            "detail": (e.read().decode("utf-8", errors="replace")[:500] if hasattr(e, "read") else str(e)),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": "runtime_unreachable",
            "detail": str(e),
            "url": url,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": "runtime_response_parse_failed",
            "detail": str(e),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    return {
        "ok": True,
        "agent": agent.name,
        "content": (data.get("choices") or [{}])[0].get("message", {}).get("content", ""),
        "finish_reason": (data.get("choices") or [{}])[0].get("finish_reason"),
        "model": data.get("model", model),
        "usage": data.get("usage"),
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dispatcher.py",
        description="Local-First Dispatcher for Agency Agents — runs any agent in this repo against an OpenAI-compatible local runtime at $0 inference cost.",
    )
    p.add_argument("--agent", help="Path to agent .md file (or dir containing one)")
    p.add_argument("--task", help="The task to send the agent")
    p.add_argument("--base-url", help="OpenAI-compatible base URL (default: $AGENCY_BASE_URL or Ollama on :11434)")
    p.add_argument("--model", help="Model id (default: $AGENCY_MODEL or llama3.1:8b)")
    p.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature (default 0.3)")
    p.add_argument("--max-tokens", type=int, default=2048, help="Cap on response tokens (default 2048)")
    p.add_argument("--json", action="store_true", help="Output full response payload as JSON")
    p.add_argument("--list", help="List agent files under a directory (no dispatch)")
    return p


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list:
        for a in list_agents(args.list):
            print(f"{a['name']:<40}  {a['description']}")
        return 0

    if not args.agent or not args.task:
        parser.print_help(sys.stderr)
        return 2

    try:
        agent = load_agent(args.agent)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    result = dispatch_agent(
        agent=agent,
        task=args.task,
        base_url=args.base_url,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if not result.get("ok"):
        detail = f" — {result.get('detail')}" if result.get("detail") else ""
        print(f"error: {result.get('error')}{detail}", file=sys.stderr)
        return 1
    print(result["content"], end="" if result["content"].endswith("\n") else "\n")
    print(
        f"\n[dispatched {agent.name} via {result.get('model')} in {result['latency_ms']}ms]",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
