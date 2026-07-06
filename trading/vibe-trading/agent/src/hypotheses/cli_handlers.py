"""CLI handlers for ``vibe-trading hypothesis {list,show,invalidate}``.

All logic lives here; ``agent/cli.py`` only wires this in via :func:`add_subparser`
and :func:`dispatch`. Handlers print to stdout (Rich when available, plain
``print`` fallback) and return an int exit code. Errors are reported as a
one-line stderr message; tracebacks are suppressed unless ``--verbose`` is set
on the namespace.

Storage path resolution defers to :func:`default_hypotheses_path`, so callers
(and tests) can override via the ``VIBE_TRADING_HYPOTHESES_PATH`` env var or by
passing ``--path``.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    _console: Console | None = Console()
except Exception:  # pragma: no cover — rich is a project dep, fallback only
    _console = None
    Table = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]

from src.hypotheses.registry import (
    HYPOTHESIS_STATUSES,
    Hypothesis,
    HypothesisRegistry,
)


_STATUS_STYLES = {
    "exploring": "cyan",
    "testing": "yellow",
    "validated": "green",
    "rejected": "red",
    "monitoring": "magenta",
}


def _print(msg: str) -> None:
    if _console is not None:
        _console.print(msg)
    else:
        print(msg)


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _registry(args: argparse.Namespace) -> HypothesisRegistry:
    override = getattr(args, "path", None)
    if override:
        return HypothesisRegistry(path=Path(override).expanduser())
    return HypothesisRegistry()


def _hypothesis_payload(hyp: Hypothesis) -> dict[str, Any]:
    return hyp.to_dict()


def _emit_table(rows: list[Hypothesis]) -> None:
    if Table is None:
        for hyp in rows:
            print(
                f"{hyp.hypothesis_id}\t{hyp.status}\t{hyp.title}\t{hyp.updated_at}"
            )
        return
    table = Table(title=f"Hypotheses ({len(rows)})", show_lines=False)
    table.add_column("ID", style="bold", overflow="fold")
    table.add_column("Status")
    table.add_column("Title", overflow="fold")
    table.add_column("Universe", overflow="fold")
    table.add_column("Run cards", justify="right")
    table.add_column("Updated", overflow="fold")
    for hyp in rows:
        status_style = _STATUS_STYLES.get(hyp.status, "white")
        table.add_row(
            hyp.hypothesis_id,
            f"[{status_style}]{hyp.status}[/{status_style}]",
            hyp.title,
            hyp.universe or "-",
            str(len(hyp.run_cards)),
            hyp.updated_at,
        )
    # Use a wide non-TTY console so piped/captured output keeps each row on
    # one line; interactive TTYs continue to honor the live terminal width
    # via the module-level _console.
    if sys.stdout.isatty() and _console is not None:
        _console.print(table)
    else:
        Console(width=200, force_terminal=False).print(table)


def _emit_detail(hyp: Hypothesis) -> None:
    if _console is None or Panel is None:
        print(json.dumps(hyp.to_dict(), ensure_ascii=False, indent=2))
        return
    status_style = _STATUS_STYLES.get(hyp.status, "white")
    body_lines = [
        f"[bold]ID:[/bold] {hyp.hypothesis_id}",
        f"[bold]Status:[/bold] [{status_style}]{hyp.status}[/{status_style}]",
        f"[bold]Universe:[/bold] {hyp.universe or '-'}",
        f"[bold]Data sources:[/bold] {', '.join(hyp.data_sources) or '-'}",
        f"[bold]Skills:[/bold] {', '.join(hyp.skills) or '-'}",
        f"[bold]Created:[/bold] {hyp.created_at}",
        f"[bold]Updated:[/bold] {hyp.updated_at}",
        "",
        "[bold]Thesis[/bold]",
        hyp.thesis or "-",
    ]
    if hyp.signal_definition:
        body_lines.extend(["", "[bold]Signal[/bold]", hyp.signal_definition])
    if hyp.invalidation_notes:
        body_lines.extend(
            ["", "[bold red]Invalidation notes[/bold red]", hyp.invalidation_notes]
        )
    if hyp.run_cards:
        body_lines.append("")
        body_lines.append(f"[bold]Linked run cards ({len(hyp.run_cards)})[/bold]")
        for idx, link in enumerate(hyp.run_cards, 1):
            run_card_path = link.get("run_card_path") or "-"
            run_dir = link.get("backtest_run_dir") or "-"
            note = link.get("notes") or ""
            linked_at = link.get("linked_at") or "-"
            body_lines.append(
                f"  {idx}. run_card={run_card_path} run_dir={run_dir} linked={linked_at}"
            )
            if note:
                body_lines.append(f"     note: {note}")
    _console.print(Panel("\n".join(body_lines), title=hyp.title, expand=False))


def _cmd_list(args: argparse.Namespace) -> int:
    registry = _registry(args)
    status_filter: str | None = getattr(args, "status", None)
    limit: int = max(0, int(getattr(args, "limit", 50) or 0))
    rows = registry.list()
    if status_filter:
        rows = [hyp for hyp in rows if hyp.status == status_filter]
    rows.sort(key=lambda h: h.updated_at, reverse=True)
    if limit:
        rows = rows[:limit]

    if getattr(args, "json", False):
        print(
            json.dumps(
                [_hypothesis_payload(hyp) for hyp in rows],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not rows:
        suffix = f" status={status_filter}" if status_filter else ""
        _print(f"No hypotheses found{suffix}.")
        return 0
    _emit_table(rows)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    registry = _registry(args)
    hypothesis_id = args.hypothesis_id
    for hyp in registry.list():
        if hyp.hypothesis_id == hypothesis_id:
            if getattr(args, "json", False):
                print(json.dumps(hyp.to_dict(), ensure_ascii=False, indent=2))
            else:
                _emit_detail(hyp)
            return 0
    _err(f"hypothesis not found: {hypothesis_id}")
    return 1


def _cmd_invalidate(args: argparse.Namespace) -> int:
    registry = _registry(args)
    note = (getattr(args, "note", "") or "").strip()
    try:
        hyp = registry.update(
            args.hypothesis_id,
            status="rejected",
            invalidation_notes=note if note else None,
        )
    except KeyError:
        _err(f"hypothesis not found: {args.hypothesis_id}")
        return 1
    except ValueError as exc:
        _err(f"invalid update: {exc}")
        return 2

    if getattr(args, "json", False):
        print(json.dumps(hyp.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print(
            f"[red]rejected[/red] {hyp.hypothesis_id} — {hyp.title}"
            + (f"\n  note: {note}" if note else "")
        )
    return 0


_DISPATCH: dict[str, Callable[[argparse.Namespace], int]] = {
    "list": _cmd_list,
    "show": _cmd_show,
    "invalidate": _cmd_invalidate,
}


_HYP_PARSER: argparse.ArgumentParser | None = None


def add_subparser(subparsers: Any) -> argparse.ArgumentParser:
    """Register ``hypothesis`` and its three sub-sub-commands on the parent
    subparsers.

    Args:
        subparsers: The object returned by ``ArgumentParser.add_subparsers(...)``.

    Returns:
        The ``hypothesis`` parser (mostly for test introspection).
    """
    global _HYP_PARSER

    hyp_parser = subparsers.add_parser(
        "hypothesis",
        help="Hypothesis Registry: list / show / invalidate",
    )
    hyp_parser.add_argument(
        "--verbose", action="store_true", help="Show full traceback on errors"
    )
    hyp_parser.add_argument(
        "--path",
        default=None,
        help=(
            "Override registry JSON path (also respects "
            "VIBE_TRADING_HYPOTHESES_PATH env var)"
        ),
    )
    hyp_sub = hyp_parser.add_subparsers(dest="hypothesis_command")

    p_list = hyp_sub.add_parser("list", help="List hypotheses")
    p_list.add_argument(
        "--status",
        choices=HYPOTHESIS_STATUSES,
        default=None,
        help="Filter by lifecycle status",
    )
    p_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum rows to print (default: 50; pass 0 for no cap)",
    )
    p_list.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON array instead of a table",
    )

    p_show = hyp_sub.add_parser("show", help="Show hypothesis detail")
    p_show.add_argument("hypothesis_id", help="Hypothesis id, e.g. hyp_abcd1234ef56")
    p_show.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON object instead of a panel",
    )

    p_invalidate = hyp_sub.add_parser(
        "invalidate", help="Mark a hypothesis as rejected with optional notes"
    )
    p_invalidate.add_argument(
        "hypothesis_id", help="Hypothesis id to invalidate"
    )
    p_invalidate.add_argument(
        "--note",
        default="",
        help="Invalidation note recorded on the hypothesis",
    )
    p_invalidate.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON object of the updated hypothesis",
    )

    _HYP_PARSER = hyp_parser
    return hyp_parser


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch ``hypothesis <sub>`` to the matching handler.

    Returns the exit code; ``cli.py`` propagates it via ``_coerce_exit_code``.
    """
    sub = getattr(args, "hypothesis_command", None)
    if sub is None:
        if _HYP_PARSER is not None:
            _HYP_PARSER.print_help()
        else:
            _err("hypothesis requires a subcommand. Try: vibe-trading hypothesis list")
        return 1
    handler = _DISPATCH.get(sub)
    if handler is None:
        _err(f"unknown hypothesis subcommand: {sub}")
        return 1
    try:
        return int(handler(args))
    except Exception as exc:  # noqa: BLE001 — surface as one-line stderr
        if getattr(args, "verbose", False):
            traceback.print_exc()
        else:
            _err(f"hypothesis {sub} failed: {exc}")
        return 1
