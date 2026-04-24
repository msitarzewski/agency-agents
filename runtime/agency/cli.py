"""Agency runtime CLI: list, run, debug, serve."""

from __future__ import annotations

import sys
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
@click.option("--show-usage/--no-show-usage", default=False,
              help="Print token usage after the run.")
@click.pass_context
def run_cmd(ctx: click.Context, request: str, skill_slug: str | None,
            session_id: str | None, workdir: Path | None,
            show_usage: bool) -> None:
    """Run REQUEST through the planner and execute it."""
    registry = _registry(ctx.obj["repo"])
    try:
        llm = _require_llm()
    except LLMError as e:
        raise click.ClickException(str(e))

    planner = Planner(registry, llm=llm)
    plan = planner.plan(request, hint_slug=skill_slug)
    click.echo(f"→ {plan.skill.emoji} {plan.skill.name} ({plan.skill.slug}) — {plan.rationale}", err=True)

    # Memory + persistence is opt-in: only wire them up when the user passes
    # --session, so ad-hoc runs don't accumulate files or enable the plan tool.
    memory: MemoryStore | None = None
    session: Session | None = None
    sid: str | None = None
    if session_id:
        sid = session_id
        memory = MemoryStore(Path.home() / ".agency" / "sessions")
        session = memory.load(sid) or Session(session_id=sid, skill_slug=plan.skill.slug)

    executor = Executor(registry, llm, memory=memory, workdir=workdir)
    result = executor.run(plan.skill, request, session=session)
    click.echo(result.text)
    if show_usage:
        u = result.usage
        click.echo(
            f"\n[usage] input={u.input_tokens} output={u.output_tokens} "
            f"cache_write={u.cache_creation_input_tokens} "
            f"cache_read={u.cache_read_input_tokens} turns={result.turns}",
            err=True,
        )
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


@main.command("init")
@click.argument("slug")
@click.option("--name", help="Human-readable name (default: derived from slug).")
@click.option("--category", default="specialized", show_default=True,
              help="Category folder under the repo root.")
@click.option("--emoji", default="🤖", show_default=True)
@click.option("--description", default="A specialized agent.", show_default=True)
@click.pass_context
def init_cmd(ctx: click.Context, slug: str, name: str | None, category: str,
             emoji: str, description: str) -> None:
    """Scaffold a new persona markdown file at <category>/<slug>.md."""
    root = ctx.obj["repo"] if ctx.obj["repo"] else discover_repo_root()
    target_dir = root / category
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{slug}.md"
    if path.exists():
        raise click.ClickException(f"{path} already exists.")
    nice_name = name or slug.replace("-", " ").title()
    body = (
        f"---\n"
        f"name: {nice_name}\n"
        f"description: {description}\n"
        f"color: cyan\n"
        f"emoji: {emoji}\n"
        f"vibe: Purpose-built specialist. Edit this file to shape its voice.\n"
        f"---\n\n"
        f"# {nice_name} Agent Personality\n\n"
        f"You are **{nice_name}**. {description}\n\n"
        f"## 🧠 Your Identity & Memory\n"
        f"- **Role**: [fill in]\n"
        f"- **Personality**: [fill in]\n\n"
        f"## 🎯 Your Core Mission\n"
        f"- [fill in]\n\n"
        f"## 🚨 Critical Rules You Must Follow\n"
        f"- [fill in]\n"
    )
    path.write_text(body, encoding="utf-8")
    click.echo(f"Created {path.relative_to(root)}")


@main.command("doctor")
@click.pass_context
def doctor_cmd(ctx: click.Context) -> None:
    """Diagnose the runtime: show what's loaded, enabled, and missing."""
    import importlib
    import os
    from .tools import ToolContext

    click.echo("=== Agency Runtime Doctor ===\n")

    # Repo + skills
    try:
        root = ctx.obj["repo"] if ctx.obj["repo"] else discover_repo_root()
        click.echo(f"repo root: {root}")
    except FileNotFoundError as e:
        click.echo(f"repo root: ERROR — {e}")
        return
    try:
        registry = SkillRegistry.load(root)
    except Exception as e:  # noqa: BLE001
        click.echo(f"skills: ERROR — {type(e).__name__}: {e}")
        return

    click.echo(f"skills loaded: {len(registry)}")
    for cat in registry.categories():
        count = len(registry.by_category(cat))
        click.echo(f"  {cat:22s}  {count}")

    # API key
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    click.echo(f"\nANTHROPIC_API_KEY: {'set ('+str(len(key))+' chars)' if key else 'NOT SET'}")

    # Env flags
    flags = [
        "AGENCY_MODEL", "AGENCY_PLANNER_MODEL", "AGENCY_MAX_TOKENS",
        "AGENCY_TASK_BUDGET", "AGENCY_MCP_SERVERS",
        "AGENCY_ENABLE_WEB_SEARCH", "AGENCY_ENABLE_CODE_EXECUTION",
        "AGENCY_ENABLE_COMPUTER_USE", "AGENCY_ALLOW_SHELL", "AGENCY_NO_NETWORK",
    ]
    click.echo("\nenv flags:")
    for f in flags:
        val = os.environ.get(f)
        click.echo(f"  {f:32s}  {val or '—'}")

    # Optional deps
    click.echo("\noptional deps:")
    for group, mods in {
        "[docs]":     ["pypdf", "docx", "openpyxl"],
        "[computer]": ["pyautogui", "PIL"],
    }.items():
        installed = []
        missing = []
        for m in mods:
            try:
                importlib.import_module(m)
                installed.append(m)
            except ImportError:
                missing.append(m)
        status = "ok" if not missing else f"missing: {', '.join(missing)}"
        click.echo(f"  {group:12s}  {status}")

    # Tool context defaults
    tc = ToolContext.from_env()
    click.echo(
        f"\ntool context:\n"
        f"  allow_shell={tc.allow_shell}  "
        f"allow_network={tc.allow_network}  "
        f"allow_computer_use={tc.allow_computer_use}  "
        f"timeout={tc.timeout_s}s"
    )

    click.echo("\nDone.")


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
        llm = AnthropicLLM(LLMConfig.from_env())
        llm._ensure_client()  # noqa: SLF001 — surface error early
        return llm
    except LLMError:
        return None


def _require_llm() -> AnthropicLLM:
    llm = AnthropicLLM(LLMConfig.from_env())
    llm._ensure_client()  # noqa: SLF001
    return llm


if __name__ == "__main__":
    sys.exit(main())
