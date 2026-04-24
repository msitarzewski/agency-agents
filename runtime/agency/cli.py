"""Agency runtime CLI: list, run, debug, serve."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import click

from .executor import Executor
from .llm import AnthropicLLM, LLMConfig, LLMError
from .memory import MemoryStore, Session
from .planner import Planner
from .skills import SkillRegistry, discover_repo_root


def _registry(repo: Path | None) -> SkillRegistry:
    root = repo if repo else discover_repo_root()
    return SkillRegistry.load(root)


@click.group()
@click.option("--repo", type=click.Path(file_okay=False, exists=True, path_type=Path),
              help="Path to the Agency repo root. Defaults to autodetect.")
@click.pass_context
def main(ctx: click.Context, repo: Path | None) -> None:
    """Agency runtime: orchestrate the persona library as runnable skills."""
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo


@main.command("list")
@click.option("--category", help="Filter to a single category (e.g., engineering).")
@click.option("--search", help="Keyword search across name/description.")
@click.pass_context
def list_cmd(ctx: click.Context, category: str | None, search: str | None) -> None:
    """List loaded skills."""
    registry = _registry(ctx.obj["repo"])
    skills = registry.search(search) if search else registry.all()
    if category:
        skills = [s for s in skills if s.category == category]
    if not skills:
        click.echo("No skills matched.")
        return
    click.echo(f"{len(skills)} skill(s):")
    for s in skills:
        click.echo(f"  {s.slug:55s}  {s.summary()}")


@main.command("plan")
@click.argument("request")
@click.option("--skill", "skill_slug", help="Force a specific skill slug (skips planner).")
@click.pass_context
def plan_cmd(ctx: click.Context, request: str, skill_slug: str | None) -> None:
    """Show which skill the planner would pick for REQUEST."""
    registry = _registry(ctx.obj["repo"])
    llm = _maybe_llm()
    planner = Planner(registry, llm=llm)
    plan = planner.plan(request, hint_slug=skill_slug)
    click.echo(f"Picked: {plan.skill.slug} — {plan.skill.name}")
    click.echo(f"Reason: {plan.rationale}")
    if len(plan.candidates) > 1:
        click.echo("Shortlist:")
        for c in plan.candidates:
            marker = "*" if c.slug == plan.skill.slug else " "
            click.echo(f"  {marker} {c.slug} — {c.name}")


@main.command("run")
@click.argument("request")
@click.option("--skill", "skill_slug", help="Force a specific skill slug (skips planner).")
@click.option("--session", "session_id", help="Session id to load/save (enables memory).")
@click.option("--workdir", type=click.Path(file_okay=False, path_type=Path),
              help="Workdir for tool calls. Defaults to current directory.")
@click.pass_context
def run_cmd(ctx: click.Context, request: str, skill_slug: str | None,
            session_id: str | None, workdir: Path | None) -> None:
    """Run REQUEST through the planner and execute it."""
    registry = _registry(ctx.obj["repo"])
    try:
        llm = _require_llm()
    except LLMError as e:
        raise click.ClickException(str(e))

    planner = Planner(registry, llm=llm)
    plan = planner.plan(request, hint_slug=skill_slug)
    click.echo(f"→ {plan.skill.emoji} {plan.skill.name} ({plan.skill.slug}) — {plan.rationale}", err=True)

    memory_root = Path.home() / ".agency" / "sessions"
    memory = MemoryStore(memory_root)
    session: Session | None = None
    sid = session_id or uuid.uuid4().hex[:12]
    if session_id:
        session = memory.load(sid) or Session(session_id=sid, skill_slug=plan.skill.slug)
    else:
        session = Session(session_id=sid, skill_slug=plan.skill.slug)

    executor = Executor(registry, llm, memory=memory, workdir=workdir)
    result = executor.run(plan.skill, request, session=session)
    click.echo(result.text)
    if session_id:
        click.echo(f"\n[session saved: {sid}]", err=True)


@main.command("debug")
@click.argument("request")
@click.option("--skill", "skill_slug", help="Force a specific skill slug.")
@click.pass_context
def debug_cmd(ctx: click.Context, request: str, skill_slug: str | None) -> None:
    """Run REQUEST and print every event (text, tool_use, tool_result)."""
    registry = _registry(ctx.obj["repo"])
    try:
        llm = _require_llm()
    except LLMError as e:
        raise click.ClickException(str(e))
    planner = Planner(registry, llm=llm)
    plan = planner.plan(request, hint_slug=skill_slug)
    click.echo(f"→ skill: {plan.skill.slug} ({plan.rationale})")
    executor = Executor(registry, llm)
    result = executor.run(plan.skill, request)
    for ev in result.events:
        if ev.kind == "text":
            click.echo(f"[text] {ev.payload}")
        elif ev.kind == "tool_use":
            click.echo(f"[tool_use] {ev.payload['name']}({ev.payload['input']})")
        elif ev.kind == "tool_result":
            tag = "tool_error" if ev.payload["is_error"] else "tool_result"
            preview = ev.payload["content"][:400]
            click.echo(f"[{tag}] {ev.payload['name']}: {preview}")
        elif ev.kind == "stop":
            click.echo(f"[stop] {ev.payload}")
    click.echo(f"\nturns: {result.turns}")


@main.command("serve")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8765, type=int)
@click.pass_context
def serve_cmd(ctx: click.Context, host: str, port: int) -> None:
    """Start the FastAPI web UI."""
    try:
        import uvicorn
    except ImportError as e:
        raise click.ClickException("uvicorn not installed. Install runtime deps.") from e
    from .server import build_app

    repo = ctx.obj["repo"]
    app = build_app(repo)
    click.echo(f"Agency runtime listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def _maybe_llm() -> AnthropicLLM | None:
    """Return an LLM client if configured, else None (for offline planning)."""
    try:
        llm = AnthropicLLM(LLMConfig())
        llm._ensure_client()  # noqa: SLF001 — surface error early
        return llm
    except LLMError:
        return None


def _require_llm() -> AnthropicLLM:
    llm = AnthropicLLM(LLMConfig())
    llm._ensure_client()  # noqa: SLF001
    return llm


if __name__ == "__main__":
    sys.exit(main())
