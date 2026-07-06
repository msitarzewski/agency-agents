"""``/goal`` — manage the current finance research goal from the CLI."""

from __future__ import annotations

import os
from typing import Any

from rich import box
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli.theme import get_console
from src.goal.context import default_goal_criteria

_goal_store = None


def _resolve_console() -> Console:
    """Return the shared CLI console."""
    return get_console()


def _get_goal_store():
    """Return the shared goal store, lazily initialized."""
    global _goal_store
    if _goal_store is None:
        from src.goal import GoalStore

        _goal_store = GoalStore()
    return _goal_store


def _default_criteria() -> list[str]:
    """Return the MVP finance protocol checklist."""
    return default_goal_criteria()


def _criterion_is_covered(criterion: dict, evidence: list[dict]) -> bool:
    """Return whether a criterion has completion status or attached evidence."""
    status = str(criterion.get("status") or "").lower()
    if status not in {"", "pending", "open", "unsatisfied"}:
        return True
    criterion_id = criterion.get("criterion_id")
    return any(item.get("criterion_id") == criterion_id for item in evidence)


def _create_cli_session(ctx: Any, title: str) -> str | None:
    """Create a normal CLI session when /goal is used before the first turn."""
    try:
        from cli._legacy import SESSIONS_DIR
        from src.session.models import Session, SessionStatus
        from src.session.search import get_shared_index
        from src.session.store import SessionStore

        session = Session(
            title=(title[:60] or "Goal research"),
            status=SessionStatus.ACTIVE,
        )
        SessionStore(base_dir=SESSIONS_DIR).create_session(session)
        get_shared_index().index_session(session.session_id, session.title)
        if ctx is not None:
            setattr(ctx, "session_id", session.session_id)
        return session.session_id
    except Exception:  # noqa: BLE001
        return None


def _session_id(ctx: Any, *, title: str = "Goal research", create: bool) -> str | None:
    """Return the active CLI session id, optionally creating one."""
    existing = getattr(ctx, "session_id", None)
    if existing:
        return str(existing)
    env_session_id = os.getenv("VIBE_GOAL_SESSION_ID")
    if env_session_id:
        return env_session_id
    if not create:
        return None
    created = _create_cli_session(ctx, title)
    if created:
        return created
    return "cli-default"


def _render_snapshot(snapshot: dict, *, title: str = "/goal") -> None:
    """Render a compact goal card."""
    console = _resolve_console()
    goal = snapshot["goal"]
    criteria = snapshot.get("criteria") or []
    evidence = snapshot.get("evidence") or []
    evidence_count = int(snapshot.get("evidence_count", len(evidence)))
    covered = sum(1 for item in criteria if _criterion_is_covered(item, evidence))
    total = len(criteria)

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim", no_wrap=True)
    meta.add_column(ratio=1)
    meta.add_column(style="dim", no_wrap=True)
    meta.add_column(no_wrap=True)
    meta.add_row("goal", str(goal["objective"]), "status", f"[green]{goal['status']}[/green]")
    meta.add_row("id", str(goal["goal_id"]), "progress", f"[cyan]{covered}/{total}[/cyan]")
    meta.add_row("evidence", str(evidence_count), "protocol", str(goal.get("protocol", "thesis_review")))

    criteria_table = Table(
        box=box.SIMPLE_HEAVY,
        show_lines=False,
        expand=True,
        padding=(0, 1),
    )
    criteria_table.add_column("#", style="dim", no_wrap=True, width=3)
    criteria_table.add_column("Criterion", ratio=1)
    criteria_table.add_column("Status", no_wrap=True)
    criteria_table.add_column("Evidence", no_wrap=True)
    for index, criterion in enumerate(criteria, start=1):
        criterion_id = criterion["criterion_id"]
        criterion_evidence = [item for item in evidence if item.get("criterion_id") == criterion_id]
        is_covered = _criterion_is_covered(criterion, evidence)
        status = "[green]covered[/green]" if is_covered else "[yellow]pending[/yellow]"
        evidence_label = (
            f"{len(criterion_evidence)} item{'s' if len(criterion_evidence) != 1 else ''}"
            if criterion_evidence
            else "[dim]needed[/dim]"
        )
        criteria_table.add_row(
            str(index),
            str(criterion["text"]),
            status,
            evidence_label,
        )
    if not criteria:
        criteria_table.add_row("-", "[dim](none)[/dim]", "[dim]pending[/dim]", "[dim]needed[/dim]")

    next_steps = Text()
    next_steps.append("Next  ", style="dim")
    next_steps.append("/goal status", style="bold")
    if criteria:
        next_steps.append("   ")
        next_steps.append("/goal evidence <#> <note>", style="bold")

    console.print(
        Panel(
            Group(meta, criteria_table, next_steps),
            title=title,
            border_style="cyan",
            padding=(1, 2),
        )
    )


def cmd_status(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Show the current goal snapshot."""
    session_id = _session_id(ctx, create=False)
    if session_id is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> to start one.", style="dim"))
        return 0
    snapshot = _get_goal_store().get_current_snapshot(session_id)
    if snapshot is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> to start one.", style="dim"))
        return 0
    _render_snapshot(snapshot)
    return 0


def cmd_start(ctx: Any = None, *args: str) -> int:
    """Start or replace the current research goal."""
    objective = " ".join(args).strip()
    if not objective:
        _resolve_console().print(Text("Usage: /goal <research objective>", style="bold red"))
        return 1

    session_id = _session_id(ctx, title=objective, create=True)
    if session_id is None:
        _resolve_console().print(Text("Could not create or resolve a session for /goal.", style="bold red"))
        return 1
    try:
        goal = _get_goal_store().replace_goal(
            session_id=session_id,
            objective=objective,
            criteria=_default_criteria(),
            source="cli",
            protocol="thesis_review",
        )
    except ValueError as exc:
        _resolve_console().print(Text(f"/goal failed: {exc}", style="bold red"))
        return 1
    snapshot = _get_goal_store().get_goal_snapshot(goal.goal_id)
    if snapshot is None:
        _resolve_console().print(Text("Goal created but could not be reloaded.", style="bold red"))
        return 1
    _render_snapshot(snapshot, title="/goal started")
    return 0


def _resolve_criterion_id(snapshot: dict, token: str) -> str:
    """Resolve a criterion by 1-based index, exact id, or id prefix."""
    criteria = snapshot.get("criteria") or []
    if token.isdigit():
        index = int(token)
        if 1 <= index <= len(criteria):
            return str(criteria[index - 1]["criterion_id"])
        raise ValueError(f"criterion index out of range: {token}")

    matches = [
        item["criterion_id"]
        for item in criteria
        if item["criterion_id"] == token or str(item["criterion_id"]).startswith(token)
    ]
    if len(matches) == 1:
        return str(matches[0])
    if not matches:
        raise ValueError(f"unknown criterion: {token}")
    raise ValueError(f"ambiguous criterion prefix: {token}")


def cmd_evidence(ctx: Any = None, *args: str) -> int:
    """Append a manual evidence note to the current goal."""
    if len(args) < 2:
        _resolve_console().print(Text("Usage: /goal evidence <criterion-index-or-id> <note>", style="bold red"))
        return 1

    session_id = _session_id(ctx, create=False)
    if session_id is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="bold red"))
        return 1
    snapshot = _get_goal_store().get_current_snapshot(session_id)
    if snapshot is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="bold red"))
        return 1

    criterion_token, *text_parts = args
    text = " ".join(text_parts).strip()
    if not text:
        _resolve_console().print(Text("Evidence note cannot be empty.", style="bold red"))
        return 1

    try:
        criterion_id = _resolve_criterion_id(snapshot, criterion_token)
        from src.goal import EvidenceInput

        _get_goal_store().append_evidence(
            session_id=session_id,
            goal_id=snapshot["goal"]["goal_id"],
            expected_goal_id=snapshot["goal"]["goal_id"],
            evidence=EvidenceInput(
                criterion_id=criterion_id,
                text=text,
                source_provider="cli",
                source_type="manual_note",
            ),
        )
    except Exception as exc:  # noqa: BLE001
        _resolve_console().print(Text(f"/goal evidence failed: {exc}", style="bold red"))
        return 1

    updated = _get_goal_store().get_goal_snapshot(snapshot["goal"]["goal_id"])
    if updated is not None:
        _render_snapshot(updated, title="/goal evidence added")
    return 0


def cmd_cancel(ctx: Any = None, *args: str) -> int:
    """Cancel the current research goal."""
    session_id = _session_id(ctx, create=False)
    if session_id is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="dim"))
        return 0
    snapshot = _get_goal_store().get_current_snapshot(session_id)
    if snapshot is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="dim"))
        return 0

    recap = " ".join(args).strip() or "Cancelled from CLI."
    try:
        from src.goal import GoalStatus

        updated = _get_goal_store().update_status(
            session_id=session_id,
            goal_id=snapshot["goal"]["goal_id"],
            expected_goal_id=snapshot["goal"]["goal_id"],
            status=GoalStatus.CANCELLED,
            recap=recap,
        )
    except Exception as exc:  # noqa: BLE001
        _resolve_console().print(Text(f"/goal cancel failed: {exc}", style="bold red"))
        return 1

    terminal_snapshot = _get_goal_store().get_goal_snapshot(updated.goal_id)
    if terminal_snapshot is not None:
        _render_snapshot(terminal_snapshot, title="/goal cancelled")
    return 0


def cmd_complete(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Complete the current research goal after auditing verified evidence."""
    session_id = _session_id(ctx, create=False)
    if session_id is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="dim"))
        return 0
    snapshot = _get_goal_store().get_current_snapshot(session_id)
    if snapshot is None:
        _resolve_console().print(Text("No current goal. Use /goal <objective> first.", style="dim"))
        return 0

    evidence = snapshot.get("evidence") or []
    audit_rows = []
    for criterion in snapshot.get("criteria") or []:
        criterion_evidence = [
            item
            for item in evidence
            if item.get("criterion_id") == criterion["criterion_id"]
            and item.get("verification_status") == "verified"
        ]
        if not criterion_evidence:
            _resolve_console().print(
                Text(
                    "Cannot complete: every criterion needs verified run/artifact evidence.",
                    style="bold red",
                )
            )
            return 1
        from src.goal import AuditRow

        audit_rows.append(
            AuditRow(
                criterion_id=criterion["criterion_id"],
                result="satisfied",
                evidence_ids=[item["evidence_id"] for item in criterion_evidence],
                notes="Verified evidence attached from CLI audit.",
            )
        )

    try:
        from src.goal import GoalStatus

        updated = _get_goal_store().update_status(
            session_id=session_id,
            goal_id=snapshot["goal"]["goal_id"],
            expected_goal_id=snapshot["goal"]["goal_id"],
            status=GoalStatus.COMPLETE,
            audit=audit_rows,
            recap=" ".join(args).strip() or "Completed from CLI audit.",
        )
    except Exception as exc:  # noqa: BLE001
        _resolve_console().print(Text(f"/goal complete failed: {exc}", style="bold red"))
        return 1

    terminal_snapshot = _get_goal_store().get_goal_snapshot(updated.goal_id)
    if terminal_snapshot is not None:
        _render_snapshot(terminal_snapshot, title="/goal completed")
    return 0


def cmd_help() -> int:
    """Render /goal usage."""
    body = Text()
    body.append("/goal <objective>", style="bold")
    body.append("  start or replace the current research goal\n", style="dim")
    body.append("/goal status", style="bold")
    body.append("  show the current goal snapshot\n", style="dim")
    body.append("/goal evidence <criterion-index-or-id> <note>", style="bold")
    body.append("  append manual evidence\n", style="dim")
    body.append("/goal complete [recap]", style="bold")
    body.append("  complete after verified evidence audit\n", style="dim")
    body.append("/goal cancel [recap]", style="bold")
    body.append("  cancel the current goal\n", style="dim")
    _resolve_console().print(Panel(body, title="/goal", border_style="dim", padding=(1, 2)))
    return 0


def run(ctx: Any = None, *args: str) -> int:
    """Dispatch /goal subcommands."""
    if not args:
        return cmd_status(ctx)

    command = args[0].lower()
    if command in {"help", "-h", "--help"}:
        return cmd_help()
    if command in {"status", "show"}:
        return cmd_status(ctx, *args[1:])
    if command == "start":
        return cmd_start(ctx, *args[1:])
    if command == "evidence":
        return cmd_evidence(ctx, *args[1:])
    if command == "complete":
        return cmd_complete(ctx, *args[1:])
    if command in {"cancel", "cancelled"}:
        return cmd_cancel(ctx, *args[1:])
    return cmd_start(ctx, *args)


__all__ = [
    "run",
    "cmd_start",
    "cmd_status",
    "cmd_evidence",
    "cmd_complete",
    "cmd_cancel",
]
