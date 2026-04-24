"""Tools the agent can call. Designed to be safe by default.

Each tool has:
 - a JSON-schema definition (fed to Claude)
 - a Python implementation that returns a string result

Shell access is gated by AGENCY_ALLOW_SHELL (default off). When enabled, only
commands whose first token is in SHELL_ALLOWLIST run. Network fetch is read-only
HTTPS GET.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

DEFAULT_SHELL_ALLOWLIST = (
    "ls", "cat", "head", "tail", "wc", "find", "grep", "rg",
    "pwd", "echo", "date", "git", "tree", "stat", "file",
    "python", "python3", "node", "npm", "pip", "uv",
    "make", "ruff", "mypy", "pytest",
)

MAX_OUTPUT_BYTES = 64_000


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable[[dict[str, Any], "ToolContext"], ToolResult]

    def to_anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolContext:
    """Per-session execution context passed to every tool call."""

    workdir: Path
    allow_shell: bool = False
    shell_allowlist: tuple[str, ...] = DEFAULT_SHELL_ALLOWLIST
    allow_network: bool = True
    timeout_s: int = 30

    @classmethod
    def from_env(cls, workdir: Path | None = None) -> "ToolContext":
        return cls(
            workdir=(workdir or Path.cwd()).resolve(),
            allow_shell=_truthy(os.environ.get("AGENCY_ALLOW_SHELL")),
            allow_network=not _truthy(os.environ.get("AGENCY_NO_NETWORK")),
            timeout_s=int(os.environ.get("AGENCY_TOOL_TIMEOUT", "30")),
        )


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "on")


def _safe_path(ctx: ToolContext, raw: str) -> Path:
    """Resolve `raw` against the workdir and reject anything escaping it."""
    candidate = (ctx.workdir / raw).resolve() if not os.path.isabs(raw) else Path(raw).resolve()
    try:
        candidate.relative_to(ctx.workdir)
    except ValueError as e:
        raise PermissionError(f"Path escapes workdir: {raw}") from e
    return candidate


def _truncate(text: str) -> str:
    if len(text.encode("utf-8", errors="ignore")) <= MAX_OUTPUT_BYTES:
        return text
    cut = text[:MAX_OUTPUT_BYTES]
    return cut + f"\n\n[... truncated, {len(text) - len(cut)} chars omitted]"


# ----- Tool implementations -----------------------------------------------

def _read_file(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    path = _safe_path(ctx, args["path"])
    if not path.exists():
        return ToolResult(f"File not found: {args['path']}", is_error=True)
    if path.is_dir():
        return ToolResult(f"Path is a directory: {args['path']}", is_error=True)
    try:
        return ToolResult(_truncate(path.read_text(encoding="utf-8", errors="replace")))
    except OSError as e:
        return ToolResult(f"Read error: {e}", is_error=True)


def _list_dir(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    path = _safe_path(ctx, args.get("path", "."))
    if not path.exists():
        return ToolResult(f"Path not found: {args.get('path', '.')}", is_error=True)
    if not path.is_dir():
        return ToolResult(f"Not a directory: {path}", is_error=True)
    entries = []
    for entry in sorted(path.iterdir()):
        kind = "d" if entry.is_dir() else "f"
        entries.append(f"{kind} {entry.name}")
    return ToolResult("\n".join(entries) or "(empty)")


def _write_file(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    path = _safe_path(ctx, args["path"])
    content = args.get("content", "")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as e:
        return ToolResult(f"Write error: {e}", is_error=True)
    return ToolResult(f"Wrote {len(content)} chars to {path.relative_to(ctx.workdir)}")


def _run_shell(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    if not ctx.allow_shell:
        return ToolResult(
            "Shell access is disabled. Set AGENCY_ALLOW_SHELL=1 to enable "
            "(commands are still gated by an allowlist).",
            is_error=True,
        )
    command = args["command"].strip()
    if not command:
        return ToolResult("Empty command.", is_error=True)
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return ToolResult(f"Could not parse command: {e}", is_error=True)
    head = tokens[0]
    if head not in ctx.shell_allowlist:
        return ToolResult(
            f"Command not in allowlist: {head}. Allowed: {', '.join(sorted(ctx.shell_allowlist))}",
            is_error=True,
        )
    if shutil.which(head) is None:
        return ToolResult(f"Executable not found: {head}", is_error=True)
    try:
        proc = subprocess.run(
            tokens,
            cwd=str(ctx.workdir),
            capture_output=True,
            text=True,
            timeout=ctx.timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(f"Timed out after {ctx.timeout_s}s.", is_error=True)
    except OSError as e:
        return ToolResult(f"Exec error: {e}", is_error=True)
    out = proc.stdout
    if proc.stderr:
        out = (out + "\n[stderr]\n" + proc.stderr) if out else proc.stderr
    out = out + f"\n[exit: {proc.returncode}]"
    return ToolResult(_truncate(out), is_error=proc.returncode != 0)


def _web_fetch(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    if not ctx.allow_network:
        return ToolResult("Network access disabled (AGENCY_NO_NETWORK).", is_error=True)
    url = args["url"]
    if not (url.startswith("https://") or url.startswith("http://")):
        return ToolResult("Only http/https URLs are allowed.", is_error=True)
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=ctx.timeout_s,
                         headers={"User-Agent": "agency-runtime/0.1"})
    except httpx.HTTPError as e:
        return ToolResult(f"Fetch error: {e}", is_error=True)
    text = resp.text
    return ToolResult(_truncate(f"HTTP {resp.status_code}\n\n{text}"))


def _list_skills(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    # Filled in at registry build time so the executor can introspect siblings.
    skills = getattr(ctx, "_skills_summary", None)
    if not skills:
        return ToolResult("No sibling skills are registered in this session.", is_error=True)
    return ToolResult(skills)


def _delegate_to_skill(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    """Invoke another skill as a subagent and return its final text.

    Requires the executor to have populated `ctx._delegate_runner`. Enforces
    a small recursion cap so delegation cycles can't explode.
    """
    runner = getattr(ctx, "_delegate_runner", None)
    if runner is None:
        return ToolResult("Delegation is not available in this session.", is_error=True)
    slug = args.get("slug", "").strip()
    request = args.get("request", "").strip()
    if not slug or not request:
        return ToolResult("delegate_to_skill requires 'slug' and 'request'.", is_error=True)
    try:
        return ToolResult(runner(slug, request))
    except KeyError as e:
        return ToolResult(f"No such skill: {e}", is_error=True)
    except RecursionError as e:
        return ToolResult(str(e), is_error=True)


def _plan_path(ctx: ToolContext) -> Path | None:
    root = getattr(ctx, "_plan_root", None)
    session_id = getattr(ctx, "_plan_session_id", None)
    if root is None or session_id is None:
        return None
    Path(root).mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "default"
    return Path(root) / f"{safe}.md"


def _plan_tool(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    """View / write / append / clear a persistent plan file for the session.

    The plan is a markdown scratchpad the agent can maintain across turns and
    re-read when starting work on a new turn. Based on the Manus-style
    planning pattern (github.com/OthmanAdi/planning-with-files).
    """
    path = _plan_path(ctx)
    if path is None:
        return ToolResult(
            "Plan is only available within a named session. Re-run with --session <id>.",
            is_error=True,
        )
    action = (args.get("action") or "view").lower().strip()
    if action == "view":
        if not path.exists():
            return ToolResult("(no plan yet)")
        return ToolResult(_truncate(path.read_text(encoding="utf-8")))
    if action == "write":
        content = args.get("content", "")
        path.write_text(content, encoding="utf-8")
        return ToolResult(f"Wrote {len(content)} chars to plan.")
    if action == "append":
        content = args.get("content", "")
        with path.open("a", encoding="utf-8") as f:
            f.write(content if content.endswith("\n") else content + "\n")
        return ToolResult(f"Appended {len(content)} chars to plan.")
    if action == "clear":
        if path.exists():
            path.unlink()
        return ToolResult("Plan cleared.")
    return ToolResult(f"Unknown action: {action}. Use view|write|append|clear.", is_error=True)


# ----- Builtin registry ----------------------------------------------------

def builtin_tools() -> list[Tool]:
    return [
        Tool(
            name="read_file",
            description="Read a UTF-8 text file from the working directory.",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path."}},
                "required": ["path"],
            },
            func=_read_file,
        ),
        Tool(
            name="list_dir",
            description="List entries in a directory under the working directory.",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
            },
            func=_list_dir,
        ),
        Tool(
            name="write_file",
            description="Create or overwrite a UTF-8 text file under the working directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            func=_write_file,
        ),
        Tool(
            name="run_shell",
            description=(
                "Run a shell command from a strict allowlist. Disabled unless "
                "AGENCY_ALLOW_SHELL=1 is set in the environment."
            ),
            input_schema={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
            func=_run_shell,
        ),
        Tool(
            name="web_fetch",
            description="Fetch the body of an HTTP/HTTPS URL (read-only GET).",
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            func=_web_fetch,
        ),
        Tool(
            name="list_skills",
            description="List the other agency skills available for delegation.",
            input_schema={"type": "object", "properties": {}},
            func=_list_skills,
        ),
        Tool(
            name="delegate_to_skill",
            description=(
                "Invoke another agency skill as a sub-agent and return its final "
                "text response. Use when a task falls outside your specialty and "
                "another skill is a better fit. Look up valid slugs with list_skills."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Target skill slug."},
                    "request": {"type": "string", "description": "Task to hand off."},
                },
                "required": ["slug", "request"],
            },
            func=_delegate_to_skill,
        ),
        Tool(
            name="plan",
            description=(
                "Read or update a persistent per-session markdown plan. Use it to "
                "decompose a task, track progress across turns, and re-read what "
                "you've committed to before acting. Actions: view | write | append "
                "| clear. Only available when a session id is set."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["view", "write", "append", "clear"],
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content for write/append.",
                    },
                },
                "required": ["action"],
            },
            func=_plan_tool,
        ),
    ]


def tools_by_name(tools: list[Tool]) -> dict[str, Tool]:
    return {t.name: t for t in tools}
