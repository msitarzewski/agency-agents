"""
XCT Agent Gateway — A2A-compatible HTTP service for xct-agents.

Each xct-agent personality is served as an A2A endpoint:
    POST /agents/{slug}/

The gateway prepends the agent's system prompt to every request, then
forwards the completion to LiteLLM (or any OpenAI-compatible endpoint).

Env vars:
    LITELLM_API_BASE   Base URL of LiteLLM proxy  (default: http://localhost:4000)
    LITELLM_API_KEY    API key for LiteLLM         (default: sk-1234)
    DEFAULT_MODEL      LLM model to use             (default: gpt-3.5-turbo)
    AGENTS_REPO_PATH   Path to xct-agents repo      (default: auto-detect)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LITELLM_BASE = os.getenv("LITELLM_API_BASE", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_API_KEY", "sk-1234")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")

AGENT_DIRS = [
    "academic", "design", "engineering", "finance", "game-development",
    "marketing", "paid-media", "product", "project-management",
    "sales", "spatial-computing", "specialized", "strategy", "support", "testing",
]


def _find_repo_root() -> Path:
    env_path = os.getenv("AGENTS_REPO_PATH")
    if env_path:
        return Path(env_path)
    # Navigate from integrations/litellm/gateway/ → repo root
    return Path(__file__).parent.parent.parent.parent


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


def load_agents(repo_root: Path) -> dict[str, dict]:
    """Return {slug: agent_dict} for all agents."""
    registry: dict[str, dict] = {}
    for cat in AGENT_DIRS:
        cat_dir = repo_root / cat
        if not cat_dir.exists():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            agent = parse_agent_file(md_file)
            if agent:
                registry[agent["slug"]] = agent
    return registry


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="XCT Agent Gateway", version="1.0.0")

AGENTS: dict[str, dict] = {}


@app.on_event("startup")
async def startup() -> None:
    global AGENTS
    repo_root = _find_repo_root()
    AGENTS = load_agents(repo_root)
    print(f"[gateway] Loaded {len(AGENTS)} agents from {repo_root}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Agent Card (A2A discovery)
# ---------------------------------------------------------------------------
@app.get("/agents/{slug}/")
async def agent_card(slug: str, request: Request) -> JSONResponse:
    agent = AGENTS.get(slug)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")

    base_url = str(request.base_url).rstrip("/")
    label = f"{agent['emoji']} {agent['name']}" if agent["emoji"] else agent["name"]
    card = {
        "protocolVersion": "1.0",
        "name": label,
        "description": agent["description"] or agent["vibe"],
        "url": f"{base_url}/agents/{slug}/",
        "version": "1.0.0",
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "capabilities": {"streaming": False},
        "skills": [
            {
                "id": slug,
                "name": agent["name"],
                "description": agent["description"] or agent["vibe"],
                "tags": [agent["category"]],
                "examples": [],
            }
        ],
    }
    return JSONResponse(card)


# ---------------------------------------------------------------------------
# Inference endpoint (A2A-compatible chat)
# ---------------------------------------------------------------------------
@app.post("/agents/{slug}/")
async def invoke_agent(slug: str, request: Request) -> JSONResponse:
    agent = AGENTS.get(slug)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")

    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Extract messages — support both A2A and OpenAI formats
    messages: list[dict] = body.get("messages", [])
    if not messages:
        # A2A format: single message in params.message.parts
        params = body.get("params", {})
        message = params.get("message", {})
        parts = message.get("parts", [])
        for part in parts:
            if part.get("kind") == "text":
                messages = [{"role": "user", "content": part["text"]}]
                break
    if not messages:
        raise HTTPException(status_code=422, detail="No messages found in request")

    # Prepend agent system prompt
    if not any(m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": agent["system_prompt"]}] + messages

    model = body.get("model", DEFAULT_MODEL)

    # Forward to LiteLLM
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    # Pass through optional params
    for key in ("temperature", "max_tokens", "top_p", "stop"):
        if key in body:
            payload[key] = body[key]

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{LITELLM_BASE}/v1/chat/completions",
                headers={"Authorization": f"Bearer {LITELLM_KEY}",
                         "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code,
                                detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"LiteLLM unreachable: {e}")

    return JSONResponse(resp.json())


# ---------------------------------------------------------------------------
# Registry listing
# ---------------------------------------------------------------------------
@app.get("/agents")
async def list_agents() -> JSONResponse:
    return JSONResponse({
        "agents": [
            {
                "slug": slug,
                "name": a["name"],
                "description": a["description"],
                "category": a["category"],
                "emoji": a["emoji"],
            }
            for slug, a in sorted(AGENTS.items())
        ],
        "total": len(AGENTS),
    })


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "agents_loaded": len(AGENTS)})
