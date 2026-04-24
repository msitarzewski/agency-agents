"""FastAPI server with a minimal chat UI for the agency runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .executor import Executor
from .llm import AnthropicLLM, LLMConfig, LLMError
from .memory import MemoryStore, Session
from .planner import Planner
from .skills import SkillRegistry, discover_repo_root


class RunRequest(BaseModel):
    message: str
    skill: str | None = None
    session_id: str | None = None


class PlanRequestBody(BaseModel):
    message: str


def build_app(repo: Path | None = None) -> FastAPI:
    root = repo if repo else discover_repo_root()
    registry = SkillRegistry.load(root)
    memory = MemoryStore(Path.home() / ".agency" / "sessions")

    app = FastAPI(title="Agency Runtime", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _CHAT_HTML

    @app.get("/api/skills")
    def list_skills() -> dict[str, Any]:
        return {
            "count": len(registry),
            "skills": [
                {
                    "slug": s.slug,
                    "name": s.name,
                    "category": s.category,
                    "description": s.description,
                    "emoji": s.emoji,
                }
                for s in registry.all()
            ],
        }

    @app.post("/api/plan")
    def plan_endpoint(body: PlanRequestBody) -> dict[str, Any]:
        llm = _maybe_llm()
        planner = Planner(registry, llm=llm)
        plan = planner.plan(body.message)
        return {
            "skill": {"slug": plan.skill.slug, "name": plan.skill.name},
            "rationale": plan.rationale,
            "candidates": [{"slug": c.slug, "name": c.name} for c in plan.candidates],
        }

    @app.post("/api/run")
    def run_endpoint(body: RunRequest) -> dict[str, Any]:
        try:
            llm = _require_llm()
        except LLMError as e:
            raise HTTPException(503, str(e))
        planner = Planner(registry, llm=llm)
        plan = planner.plan(body.message, hint_slug=body.skill)

        session: Session | None = None
        if body.session_id:
            session = memory.load(body.session_id) or Session(
                session_id=body.session_id, skill_slug=plan.skill.slug
            )

        executor = Executor(registry, llm, memory=memory)
        result = executor.run(plan.skill, body.message, session=session)
        return {
            "skill": {"slug": plan.skill.slug, "name": plan.skill.name, "emoji": plan.skill.emoji},
            "rationale": plan.rationale,
            "text": result.text,
            "turns": result.turns,
            "session_id": session.session_id if session else None,
        }

    return app


def _maybe_llm() -> AnthropicLLM | None:
    try:
        llm = AnthropicLLM(LLMConfig())
        llm._ensure_client()  # noqa: SLF001
        return llm
    except LLMError:
        return None


def _require_llm() -> AnthropicLLM:
    llm = AnthropicLLM(LLMConfig())
    llm._ensure_client()  # noqa: SLF001
    return llm


_CHAT_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Agency Runtime</title>
  <style>
    :root { color-scheme: light dark; }
    body { font: 15px/1.5 system-ui, sans-serif; max-width: 820px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 4px; }
    .sub { color: #888; margin-bottom: 16px; }
    .row { display: flex; gap: 8px; margin: 12px 0; }
    select, input, textarea, button {
      font: inherit; padding: 8px 10px; border-radius: 6px; border: 1px solid #999;
      background: transparent; color: inherit;
    }
    textarea { width: 100%; min-height: 80px; }
    button { cursor: pointer; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    #log { margin-top: 16px; border: 1px solid #444; border-radius: 6px; padding: 12px;
           white-space: pre-wrap; min-height: 200px; }
    .meta { color: #888; font-size: 13px; }
  </style>
</head>
<body>
  <h1>The Agency</h1>
  <div class="sub">Pick a skill or let the planner choose, then send a request.</div>
  <div class="row">
    <select id="skill"><option value="">(auto-route)</option></select>
    <input id="session" placeholder="session id (optional)" />
  </div>
  <textarea id="msg" placeholder="What would you like the agent to do?"></textarea>
  <div class="row">
    <button id="send">Send</button>
    <span id="status" class="meta"></span>
  </div>
  <div id="log"></div>
<script>
  async function loadSkills() {
    const r = await fetch("/api/skills");
    const data = await r.json();
    const sel = document.getElementById("skill");
    for (const s of data.skills) {
      const opt = document.createElement("option");
      opt.value = s.slug;
      opt.textContent = `${s.emoji} ${s.name} (${s.category})`;
      sel.appendChild(opt);
    }
    document.getElementById("status").textContent = `${data.count} skills loaded`;
  }
  async function send() {
    const btn = document.getElementById("send");
    const log = document.getElementById("log");
    const msg = document.getElementById("msg").value.trim();
    if (!msg) return;
    btn.disabled = true;
    document.getElementById("status").textContent = "thinking…";
    log.textContent = "";
    try {
      const r = await fetch("/api/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message: msg,
          skill: document.getElementById("skill").value || null,
          session_id: document.getElementById("session").value || null,
        }),
      });
      if (!r.ok) {
        const text = await r.text();
        log.textContent = `Error ${r.status}: ${text}`;
        return;
      }
      const data = await r.json();
      log.textContent =
        `→ ${data.skill.emoji} ${data.skill.name} (${data.skill.slug})\\n` +
        `   ${data.rationale}\\n\\n${data.text}\\n\\n[${data.turns} turn(s)]`;
    } catch (e) {
      log.textContent = `Network error: ${e}`;
    } finally {
      btn.disabled = false;
      document.getElementById("status").textContent = "";
    }
  }
  document.getElementById("send").addEventListener("click", send);
  loadSkills();
</script>
</body>
</html>
"""
