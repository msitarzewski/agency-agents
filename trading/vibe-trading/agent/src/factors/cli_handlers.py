"""CLI handlers for ``vibe-trading alpha {list,show,bench,compare,export-manifest}``.

All logic lives here; ``agent/cli.py`` only wires this in via :func:`add_subparser`
and :func:`dispatch`. Handlers print to stdout (Rich when available, plain
``print`` fallback) and return an int exit code. Errors are reported as a
one-line stderr message; tracebacks are suppressed unless ``--verbose`` is set
on the namespace.

Security gates:
    * ``alpha show <id>`` validates ``id`` against ``Registry().list()`` before
      touching the filesystem.
    * ``alpha export-manifest --out PATH`` refuses to write outside the repo
      root (``Path(__file__).resolve().parents[3]``) unless ``--force``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# Silence the noisy ConstantInputWarning that scipy emits from spearmanr when
# the IC slice has zero variance (very common in alpha bench loops).
try:
    from scipy.stats import ConstantInputWarning  # type: ignore[attr-defined]

    warnings.filterwarnings("ignore", category=ConstantInputWarning)
except Exception:  # pragma: no cover — older scipy / unexpected layout
    try:
        from scipy.stats._warnings_errors import (  # type: ignore[attr-defined]
            ConstantInputWarning,
        )

        warnings.filterwarnings("ignore", category=ConstantInputWarning)
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.syntax import Syntax
    from rich.table import Table

    _console: Console | None = Console()
except Exception:  # pragma: no cover — rich is a project dep, fallback only
    _console = None
    Syntax = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    BarColumn = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]

from src.factors.compare_runner import SORT_KEYS as _COMPARE_SORT_KEYS, compare_alphas
from src.factors.registry import Registry, RegistryError


# Resolve repo root once: this file lives at
# ``<repo>/agent/src/factors/cli_handlers.py``; parents[3] is the repo root.
# We treat ``<repo>`` (and any subdirectory thereof) as the write-allow root.
_REPO_ROOT = Path(__file__).resolve().parents[3]

_UNIVERSE_CHOICES = ["csi300", "sp500", "btc-usdt"]


def _print(msg: str) -> None:
    if _console is not None:
        _console.print(msg)
    else:
        print(msg)


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _stdout_is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:  # noqa: BLE001
        return False


_stderr_console: Console | None = None
if _console is not None:
    try:
        _stderr_console = Console(stderr=True)
    except Exception:  # noqa: BLE001
        _stderr_console = None


def _hint(msg: str) -> None:
    """Print a next-step hint to stderr when stdout is a TTY.

    Goes to stderr so it does not pollute JSON / pipe-friendly stdout output.
    """
    if not _stdout_is_tty():
        return
    if _stderr_console is not None:
        _stderr_console.print(f"[dim]{msg}[/dim]")
    else:
        print(msg, file=sys.stderr)


def _handle_exception(args: argparse.Namespace, prefix: str, exc: BaseException) -> int:
    """Print one-line error; emit traceback only when ``--verbose`` is set."""
    _err(f"{prefix}: {exc}")
    if getattr(args, "verbose", False):
        traceback.print_exception(type(exc), exc, exc.__traceback__)
    # Surface a helpful banner for the common TUSHARE_TOKEN error case.
    if "TUSHARE_TOKEN" in str(exc):
        _err("")
        _err("How to fix:")
        _err("  1. Register for a free token at https://tushare.pro/register")
        _err("  2. Add 'TUSHARE_TOKEN=<your_token>' to agent/.env  (or ~/.vibe-trading/.env)")
        _err("  3. Re-run this command")
    return 1


# --------------------------------------------------------------------------- #
# Handlers                                                                    #
# --------------------------------------------------------------------------- #


def cmd_alpha_list(args: argparse.Namespace) -> int:
    """``vibe-trading alpha list [--zoo X] [--theme Y] [--universe Z]``.

    Supports ``--limit N`` (default 50) and ``--json`` for machine-readable
    output. ``--include-load-errors`` (alias: ``--show-failed``) appends a
    registry health block.
    """
    try:
        reg = Registry()
        ids = reg.list(zoo=args.zoo, theme=args.theme, universe=args.universe)

        limit = getattr(args, "limit", None)
        total = len(ids)
        truncated = False
        # limit > 0 => cap; limit == 0 / None => no cap.
        if isinstance(limit, int) and limit > 0 and total > limit:
            ids = ids[:limit]
            truncated = True

        # JSON mode: machine-readable, no Rich, no hints.
        if getattr(args, "json", False):
            records: list[dict[str, Any]] = []
            for alpha_id in ids:
                alpha = reg.get(alpha_id)
                meta = alpha.meta or {}
                records.append(
                    {
                        "id": alpha.id,
                        "zoo": alpha.zoo,
                        "theme": meta.get("theme", []) or [],
                        "universe": meta.get("universe", []) or [],
                        "decay_horizon": meta.get("decay_horizon"),
                    }
                )
            print(json.dumps(records, indent=2, default=str))
            if _include_load_errors(args):
                _print_load_errors(reg)
            return 0

        if not ids:
            _print("[dim]no alphas matched the filters[/dim]" if _console else "no alphas matched the filters")
        elif _console is not None and Table is not None:
            title = f"Alpha Zoo ({len(ids)} of {total} alphas)" if truncated else f"Alpha Zoo ({total} alphas)"
            table = Table(title=title)
            table.add_column("id", style="cyan", no_wrap=True)
            table.add_column("zoo", style="magenta")
            table.add_column("theme")
            table.add_column("universe")
            table.add_column("nickname")
            for alpha_id in ids:
                alpha = reg.get(alpha_id)
                meta = alpha.meta
                table.add_row(
                    alpha.id,
                    alpha.zoo,
                    ", ".join(meta.get("theme", []) or []),
                    ", ".join(meta.get("universe", []) or []),
                    meta.get("nickname") or "",
                )
            _console.print(table)
            if truncated:
                _print(f"[dim]Showing {len(ids)} of {total}. Pass --limit N (or --limit 0 for no cap).[/dim]")
        else:
            for alpha_id in ids:
                alpha = reg.get(alpha_id)
                meta = alpha.meta
                print(
                    f"{alpha.id}\t{alpha.zoo}\t"
                    f"{','.join(meta.get('theme', []) or [])}\t"
                    f"{','.join(meta.get('universe', []) or [])}\t"
                    f"{meta.get('nickname') or ''}"
                )
            if truncated:
                print(f"[showing {len(ids)} of {total}]")

        if _include_load_errors(args):
            _print_load_errors(reg)

        if ids:
            example_id = ids[0]
            example_zoo = reg.get(example_id).zoo
            _hint(
                f"Next: vibe-trading alpha show {example_id}  |  "
                f"Bench a zoo: vibe-trading alpha bench --zoo {example_zoo} "
                f"--universe csi300 --period 2020-2025"
            )
        return 0
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(args, "alpha list failed", exc)


def _include_load_errors(args: argparse.Namespace) -> bool:
    """Honour both the new flag name and the deprecated alias."""
    return bool(getattr(args, "include_load_errors", False) or getattr(args, "show_failed", False))


def _print_load_errors(reg: Registry) -> None:
    health = reg.health()
    errors = health.get("errors", [])
    if not errors:
        _print("[green]no load errors[/green]" if _console else "no load errors")
        return
    _print(
        f"[yellow]{len(errors)} load error(s):[/yellow]"
        if _console
        else f"{len(errors)} load error(s):"
    )
    for entry in errors:
        _print(f"  - {entry.get('alpha_id')}: {entry.get('reason')}")


def cmd_alpha_show(args: argparse.Namespace) -> int:
    """``vibe-trading alpha show <alpha_id> [--brief]`` — metadata + source."""
    try:
        reg = Registry()
        if args.alpha_id not in reg.list():
            _err(f"alpha id not found: {args.alpha_id}")
            return 1

        alpha = reg.get(args.alpha_id)
        meta = alpha.meta
        brief = bool(getattr(args, "brief", False))

        _print(f"[bold cyan]id[/bold cyan]: {alpha.id}" if _console else f"id: {alpha.id}")
        if not brief:
            _print(f"[bold]zoo[/bold]: {alpha.zoo}" if _console else f"zoo: {alpha.zoo}")
            _print(
                f"[bold]module_path[/bold]: {alpha.module_path}"
                if _console
                else f"module_path: {alpha.module_path}"
            )
            _print(
                f"[bold]nickname[/bold]: {meta.get('nickname') or '-'}"
                if _console
                else f"nickname: {meta.get('nickname') or '-'}"
            )
        _print(
            f"[bold]theme[/bold]: {', '.join(meta.get('theme', []) or [])}"
            if _console
            else f"theme: {', '.join(meta.get('theme', []) or [])}"
        )
        _print(
            f"[bold]universe[/bold]: {', '.join(meta.get('universe', []) or [])}"
            if _console
            else f"universe: {', '.join(meta.get('universe', []) or [])}"
        )
        if not brief:
            _print(
                f"[bold]columns_required[/bold]: {', '.join(meta.get('columns_required', []) or [])}"
                if _console
                else f"columns_required: {', '.join(meta.get('columns_required', []) or [])}"
            )
            _print(
                f"[bold]decay_horizon[/bold]: {meta.get('decay_horizon')}"
                if _console
                else f"decay_horizon: {meta.get('decay_horizon')}"
            )
        _print(
            f"[bold]formula_latex[/bold]: {meta.get('formula_latex', '')}"
            if _console
            else f"formula_latex: {meta.get('formula_latex', '')}"
        )
        notes = meta.get("notes") or ""
        if notes:
            _print(f"[bold]notes[/bold]: {notes}" if _console else f"notes: {notes}")

        if brief:
            _hint(
                f"Next: vibe-trading alpha bench --zoo {alpha.zoo} "
                f"--universe csi300 --period 2020-2025 --top 20"
            )
            return 0

        # Source code — read via the registry's _py_paths cache (semi-private but
        # accepted in the parcel contract; falls back to importlib.getsource).
        py_path: Path | None = reg._py_paths.get(alpha.id)  # noqa: SLF001
        source: str | None = None
        if py_path is not None and py_path.is_file():
            try:
                source = py_path.read_text(encoding="utf-8")
            except OSError as exc:
                _err(f"warning: could not read source file {py_path}: {exc}")
        if source is None:
            try:
                import importlib
                import inspect

                module = importlib.import_module(alpha.module_path)
                source = inspect.getsource(module)
            except Exception as exc:  # noqa: BLE001
                _err(f"warning: could not load source via importlib: {exc}")
                source = None

        if source:
            _print("[bold]source[/bold]:" if _console else "source:")
            if _console is not None and Syntax is not None:
                try:
                    _console.print(
                        Syntax(
                            source,
                            "python",
                            line_numbers=True,
                            theme="monokai",
                            word_wrap=True,
                        ),
                        soft_wrap=True,
                    )
                except Exception:  # noqa: BLE001 — fall back to raw print
                    print(source)
            else:
                print(source)

        _hint(
            f"Next: vibe-trading alpha bench --zoo {alpha.zoo} "
            f"--universe csi300 --period 2020-2025 --top 20"
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(args, "alpha show failed", exc)


def _confirm_bench_all(n_total: int) -> bool:
    """Interactive y/N prompt before benching every alpha."""
    msg = f"About to bench {n_total} alphas (~10-15 min). Continue? [y/N] "
    try:
        reply = input(msg).strip().lower()
    except EOFError:
        return False
    return reply in {"y", "yes"}


def _zoo_for_id(reg: Registry, alpha_id: str | None) -> str:
    """Lookup an alpha's zoo (best-effort, returns '' on failure)."""
    if not alpha_id:
        return ""
    try:
        return reg.get(alpha_id).zoo
    except Exception:  # noqa: BLE001
        return ""


def _run_single_zoo_with_progress(
    *,
    zoo: str,
    universe: str,
    period: str,
    top: int,
    n_target: int,
    reg: Registry,
    run_bench: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Run :func:`bench_runner.run_bench` for one zoo with a Rich progress bar."""
    if _console is None or Progress is None:
        return run_bench(
            zoo=zoo,
            universe=universe,
            period=period,
            top=top,
            registry=reg,
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TextColumn("[cyan]{task.fields[current]}[/cyan]"),
        TimeElapsedColumn(),
        console=_console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(
            description="Benching",
            total=n_target,
            current="loading universe...",
        )

        def on_progress(n_done: int, n_total: int, aid: str) -> None:
            progress.update(task_id, completed=n_done, total=n_total, current=aid)

        return run_bench(
            zoo=zoo,
            universe=universe,
            period=period,
            top=top,
            on_progress=on_progress,
            registry=reg,
        )


def _run_all_zoos_with_progress(
    *,
    target_ids: list[str],
    universe: str,
    period: str,
    top: int,
    start_ts: float,
    reg: Registry,
    run_bench: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate across every zoo for the ``--yes`` / no-``--zoo`` case."""
    zoos = sorted({reg.get(aid).zoo for aid in target_ids})
    total_alphas = sum(len(reg.list(zoo=z)) for z in zoos)
    all_rows: list[dict[str, Any]] = []
    all_skipped: list[dict[str, Any]] = []

    def _run_zoo(z: str, base: int, update: Callable[[int, str], None] | None) -> None:
        cb: Callable[[int, int, str], None] | None = None
        if update is not None:
            def cb(n_done: int, _n_total: int, aid: str) -> None:
                update(base + n_done, f"{z}:{aid}")
        sub = run_bench(
            zoo=z,
            universe=universe,
            period=period,
            top=top,
            on_progress=cb,
            registry=reg,
        )
        if sub.get("status") == "ok":
            all_rows.extend(sub.get("rows", []) or [])
            all_skipped.extend(sub.get("skipped", []) or [])
        else:
            all_skipped.append({"id": f"<zoo:{z}>", "reason": sub.get("error", "unknown")})

    if _console is not None and Progress is not None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("[cyan]{task.fields[current]}[/cyan]"),
            TimeElapsedColumn(),
            console=_console,
            transient=False,
        ) as progress:
            task_id = progress.add_task(
                description="Benching (all zoos)",
                total=total_alphas,
                current="starting...",
            )

            def update(done: int, current: str) -> None:
                progress.update(task_id, completed=done, current=current)

            seen = 0
            for z in zoos:
                _run_zoo(z, seen, update)
                seen += len(reg.list(zoo=z))
    else:
        for z in zoos:
            _run_zoo(z, 0, None)

    return {
        "status": "ok" if all_rows else "error",
        "zoo": "all",
        "universe": universe,
        "period": period,
        "rows": all_rows,
        "skipped": all_skipped,
        "n_alphas_tested": len(all_rows),
        "n_skipped": len(all_skipped),
        "wall_seconds": round(time.monotonic() - start_ts, 2),
        **({"error": "no alphas produced IC across any zoo"} if not all_rows else {}),
    }


def cmd_alpha_bench(args: argparse.Namespace) -> int:
    """``vibe-trading alpha bench --zoo X --universe csi300 --period Y-Z [--top N]``.

    Calls :func:`src.factors.bench_runner.run_bench` for the IC loop so we can
    stream Rich progress, then renders the HTML report via helpers imported
    from ``src.tools.alpha_bench_tool`` (we do NOT modify that module).
    """
    try:
        try:
            from src.factors.bench_runner import run_bench
        except ImportError as exc:
            _err(f"alpha bench failed: bench_runner unavailable ({exc})")
            return 1

        # --- 1. Decide which zoo to run (handle no-args footgun) ----------- #
        zoo = args.zoo
        if zoo is None:
            reg = Registry()
            n_total = len(reg.list())
            if getattr(args, "yes", False):
                _print(
                    f"[yellow]No --zoo passed; benching ALL {n_total} alphas "
                    f"(confirmed via --yes).[/yellow]"
                    if _console
                    else f"No --zoo passed; benching ALL {n_total} alphas (--yes)."
                )
            else:
                _print(
                    f"[yellow]Warning:[/yellow] no --zoo passed; this would bench "
                    f"every registered alpha ({n_total} total)."
                    if _console
                    else f"Warning: no --zoo passed; this would bench every alpha ({n_total})."
                )
                if not _confirm_bench_all(n_total):
                    _err("alpha bench: aborted (pass --zoo <id> or --yes to confirm).")
                    return 1

        # --- 2. Pre-flight banner: counts + ETA ---------------------------- #
        reg = Registry()
        if zoo is not None:
            target_ids = reg.list(zoo=zoo)
        else:
            target_ids = reg.list()
        n_target = len(target_ids)
        if n_target == 0:
            _err(f"alpha bench failed: no alphas registered under zoo={zoo!r}")
            return 1

        _print(
            f"[bold]Bench:[/bold] {n_target} alphas x {args.universe} x {args.period}"
            if _console
            else f"Bench: {n_target} alphas x {args.universe} x {args.period}"
        )
        _print(
            "[dim]ETA: ~3-5 min (cache hit) / ~10-20 min (cold fetch)[/dim]"
            if _console
            else "ETA: ~3-5 min (cache hit) / ~10-20 min (cold fetch)"
        )

        # --- 3. Run the bench loop with a live progress bar --------------- #
        start_ts = time.monotonic()
        result: dict[str, Any]

        if zoo is not None:
            # Single-zoo path: one call to bench_runner.run_bench.
            result = _run_single_zoo_with_progress(
                zoo=zoo,
                universe=args.universe,
                period=args.period,
                top=args.top,
                n_target=n_target,
                reg=reg,
                run_bench=run_bench,
            )
        else:
            # Multi-zoo path: aggregate across every zoo (bench_runner requires
            # a non-empty zoo, so we loop per zoo and merge).
            result = _run_all_zoos_with_progress(
                target_ids=target_ids,
                universe=args.universe,
                period=args.period,
                top=args.top,
                start_ts=start_ts,
                reg=reg,
                run_bench=run_bench,
            )

        # --- 5. Handle bench-loop errors / propagate exit code ------------- #
        status = result.get("status")
        if status != "ok":
            err_msg = result.get("error", "unknown error")
            envelope = {
                "status": "error",
                "error": err_msg,
                "zoo": zoo,
                "universe": args.universe,
                "period": args.period,
            }
            print(json.dumps(envelope, indent=2, default=str))
            _err(f"alpha bench failed: {err_msg}")
            if "TUSHARE_TOKEN" in str(err_msg):
                _err("")
                _err("How to fix:")
                _err("  1. Register for a free token at https://tushare.pro/register")
                _err("  2. Add 'TUSHARE_TOKEN=<your_token>' to agent/.env  (or ~/.vibe-trading/.env)")
                _err("  3. Re-run this command")
            return 1

        # --- 6. Render HTML report (delegating to alpha_bench_tool helpers) -#
        rows = result.get("rows", []) or []
        skipped = result.get("skipped", []) or []
        top_n = max(1, int(args.top))
        rows_sorted = sorted(rows, key=lambda r: r.get("ir", 0.0), reverse=True)
        top_rows_raw = rows_sorted[:top_n]

        # Normalise rows + skipped for the report template (and for the JSON
        # envelope so consumers don't see the internal _category key).
        def _normalise_row(r: dict[str, Any]) -> dict[str, Any]:
            return {
                "id": r.get("id"),
                "zoo": r.get("zoo") or _zoo_for_id(reg, r.get("id")),
                "theme": r.get("theme") or [],
                "formula_latex": r.get("formula_latex", ""),
                "ic_mean": r.get("ic_mean", 0.0),
                "ic_std": r.get("ic_std", 0.0),
                "ir": r.get("ir", 0.0),
                "ic_positive_ratio": r.get("ic_positive_ratio", 0.0),
                "ic_count": r.get("ic_count", 0),
                "category": r.get("_category") or r.get("category"),
            }

        def _normalise_skipped(s: dict[str, Any]) -> dict[str, Any]:
            return {"alpha_id": s.get("id") or s.get("alpha_id"), "reason": s.get("reason", "")}

        top_rows = [_normalise_row(r) for r in top_rows_raw]
        failures_for_report = [_normalise_skipped(s) for s in skipped[:10]]

        report_path: Path | None = None
        try:
            from src.tools.alpha_bench_tool import (  # type: ignore[import-not-found]
                _CSP,
                _REPORT_CSS,
                _default_output_dir,
                _render_html,
            )

            output_dir = _default_output_dir()
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            report_path = output_dir / f"alpha_bench_{ts}.html"
            context = {
                "csp": _CSP,
                "css": _REPORT_CSS,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "universe": args.universe,
                "period": args.period,
                "n_alphas_tested": len(rows),
                "n_skipped": len(skipped),
                "top": top_rows,
                "failures": failures_for_report,
            }
            report_path.write_text(_render_html(context), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 — report is nice-to-have
            _err(f"warning: could not write HTML report: {exc}")
            report_path = None

        envelope: dict[str, Any] = {
            "status": "ok",
            "zoo": zoo,
            "universe": args.universe,
            "period": args.period,
            "n_alphas_tested": len(rows),
            "n_skipped": len(skipped),
            "top": top_rows,
            "wall_seconds": result.get("wall_seconds"),
        }
        if report_path is not None:
            envelope["report_path"] = str(report_path)
        print(json.dumps(envelope, indent=2, default=str))

        # Final stderr success line (M4).
        tested = len(rows)
        skipped_n = len(skipped)
        summary = f"✓ Bench complete. {tested} tested, {skipped_n} skipped."
        if report_path is not None:
            summary += f" Report: {report_path}"
        if _stderr_console is not None:
            _stderr_console.print(summary, style="green")
        else:
            print(summary, file=sys.stderr)
        return 0
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(args, "alpha bench failed", exc)


def _render_compare_table(ranking: list[dict[str, Any]], sort_key: str) -> None:
    """Print a head-to-head ranking table to stderr (nice-to-have, never fatal)."""
    if _stderr_console is None or Table is None:
        return
    delta_key = f"delta_{sort_key}_vs_best"
    table = Table(title=f"alpha compare — ranked by {sort_key}")
    for col, justify in (
        ("#", "right"), ("alpha", "left"), ("zoo", "left"), ("IC mean", "right"),
        ("IC std", "right"), ("IR", "right"), ("IC>0", "right"), ("n", "right"),
        (f"Δ {sort_key}", "right"),
    ):
        table.add_column(col, justify=justify)
    for r in ranking:
        table.add_row(
            str(r["rank"]),
            str(r["id"]),
            str(r.get("zoo") or ""),
            f"{r.get('ic_mean', 0.0):.4f}",
            f"{r.get('ic_std', 0.0):.4f}",
            f"{r.get('ir', 0.0):.4f}",
            f"{r.get('ic_positive_ratio', 0.0):.3f}",
            str(r.get("ic_count", 0)),
            f"{r.get(delta_key, 0.0):+.4f}",
        )
    _stderr_console.print(table)


def cmd_alpha_compare(args: argparse.Namespace) -> int:
    """``vibe-trading alpha compare <id1> <id2> ... | --all | --zoo X``.

    Bench a hand-picked set of alphas head-to-head and print a ranked
    comparison (IC mean/std, IR, IC>0 ratio, sample count) plus a JSON
    envelope. Only the named alphas are evaluated — the zoo-wide loop is
    restricted via ``run_bench(only=...)`` — so comparing three alphas does
    not bench all 191 in their zoo.
    """
    try:
        reg = Registry()
        if getattr(args, "compare_all", False):
            targets = reg.list()
        elif args.zoo:
            targets = reg.list(zoo=args.zoo)
        else:
            targets = list(args.alpha_ids or [])

        # De-duplicate, preserving first-seen order.
        seen: set[str] = set()
        targets = [t for t in targets if not (t in seen or seen.add(t))]

        if not targets:
            _err(
                "alpha compare: no targets supplied "
                "(pass alpha ids, or --all for every alpha, or --zoo X to filter)"
            )
            return 1
        if len(targets) < 2:
            _err(
                f"alpha compare: need at least 2 alphas to compare "
                f"(got {len(targets)}: {', '.join(targets)})"
            )
            return 1

        sort_key = getattr(args, "sort", "ir") or "ir"
        envelope = compare_alphas(
            targets, args.universe, args.period, sort=sort_key, registry=reg
        )
        print(json.dumps(envelope, indent=2, default=str))

        if envelope.get("status") != "ok":
            _err(f"alpha compare: {envelope.get('error', 'comparison failed')}")
            return 1

        ranking = envelope["ranking"]
        _render_compare_table(ranking, sort_key)
        summary = (
            f"✓ Compared {envelope['n_compared']} alphas — winner: {envelope['winner']} "
            f"({sort_key}={ranking[0].get(sort_key, 0.0):.4f})"
        )
        if envelope["n_skipped"]:
            summary += f"; {envelope['n_skipped']} skipped"
        if _stderr_console is not None:
            _stderr_console.print(summary, style="green")
        else:
            print(summary, file=sys.stderr)
        return 0
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(args, "alpha compare failed", exc)


def cmd_alpha_export_manifest(args: argparse.Namespace) -> int:
    """``vibe-trading alpha export-manifest --out PATH [--force]``."""
    try:
        out_path = Path(args.out).resolve()

        # Refuse to write outside the repo root unless --force.
        try:
            out_path.relative_to(_REPO_ROOT)
            inside_repo = True
        except ValueError:
            inside_repo = False
        if not inside_repo and not args.force:
            _err(
                f"alpha export-manifest: refusing to write outside repo root "
                f"({_REPO_ROOT}); pass --force to override. target={out_path}"
            )
            return 1

        parent = out_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

        reg = Registry()
        manifest = reg.export_manifest()
        out_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        _print(
            f"[green]wrote manifest[/green] ({manifest['health']['loaded']} alphas, "
            f"{manifest['health']['failed']} errors) -> {out_path}"
            if _console
            else f"wrote manifest ({manifest['health']['loaded']} alphas, "
            f"{manifest['health']['failed']} errors) -> {out_path}"
        )
        return 0
    except (RegistryError, OSError) as exc:
        return _handle_exception(args, "alpha export-manifest failed", exc)
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(args, "alpha export-manifest failed", exc)


# --------------------------------------------------------------------------- #
# Subparser + dispatch wiring                                                 #
# --------------------------------------------------------------------------- #


_DISPATCH: dict[str, Callable[[argparse.Namespace], int]] = {
    "list": cmd_alpha_list,
    "show": cmd_alpha_show,
    "bench": cmd_alpha_bench,
    "compare": cmd_alpha_compare,
    "export-manifest": cmd_alpha_export_manifest,
}


# Module-level handle to the alpha parser so ``dispatch`` can print full help
# when no subcommand is supplied (M6).
_ALPHA_PARSER: argparse.ArgumentParser | None = None


def add_subparser(subparsers: Any) -> argparse.ArgumentParser:
    """Register ``alpha`` and its five sub-sub-commands on the given subparsers.

    Args:
        subparsers: The object returned by ``ArgumentParser.add_subparsers(...)``.

    Returns:
        The ``alpha`` parser (mostly for test introspection).
    """
    global _ALPHA_PARSER

    alpha_parser = subparsers.add_parser(
        "alpha", help="Alpha Zoo: list / show / bench / compare / export-manifest"
    )
    alpha_parser.add_argument(
        "--verbose", action="store_true", help="Show full traceback on errors"
    )
    alpha_sub = alpha_parser.add_subparsers(dest="alpha_command")

    p_list = alpha_sub.add_parser("list", help="List registered alphas")
    p_list.add_argument("--zoo", default=None, help="Filter by zoo (e.g. alpha101)")
    p_list.add_argument("--theme", default=None, help="Filter by theme (e.g. momentum)")
    p_list.add_argument(
        "--universe",
        default=None,
        choices=_UNIVERSE_CHOICES,
        help=f"Filter by universe ({', '.join(_UNIVERSE_CHOICES)})",
    )
    p_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max alphas to print (default: 50; pass 0 for no cap)",
    )
    p_list.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON array of {id, zoo, theme, universe, decay_horizon} instead of a table",
    )
    p_list.add_argument(
        "--include-load-errors",
        dest="include_load_errors",
        action="store_true",
        help="Also print load errors from registry.health()",
    )
    p_list.add_argument(
        "--show-failed",
        dest="show_failed",
        action="store_true",
        help="(deprecated) alias for --include-load-errors",
    )

    p_show = alpha_sub.add_parser("show", help="Show alpha metadata and source code")
    p_show.add_argument("alpha_id", help="Alpha id, e.g. alpha101_001")
    p_show.add_argument(
        "--brief",
        action="store_true",
        help="Print only id/theme/universe/formula_latex/notes — omit source code",
    )

    p_bench = alpha_sub.add_parser("bench", help="Benchmark alphas in a zoo")
    p_bench.add_argument("--zoo", default=None, help="Zoo to benchmark (required unless --yes is passed)")
    p_bench.add_argument(
        "--universe",
        default="csi300",
        choices=_UNIVERSE_CHOICES,
        help=f"Universe (default: csi300; one of {', '.join(_UNIVERSE_CHOICES)})",
    )
    p_bench.add_argument(
        "--period",
        default="2020-2025",
        help="Period spec: YYYY-YYYY or YYYY-MM-DD/YYYY-MM-DD (e.g. 2020-2025)",
    )
    p_bench.add_argument("--top", type=int, default=20, help="Top-N alphas to keep (default: 20)")
    p_bench.add_argument(
        "--yes",
        action="store_true",
        help="Skip the 'bench every alpha?' prompt when --zoo is omitted",
    )

    p_compare = alpha_sub.add_parser("compare", help="Compare alphas head-to-head")
    p_compare.add_argument("alpha_ids", nargs="*", help="Alpha ids to compare (>= 2)")
    p_compare.add_argument(
        "--all",
        dest="compare_all",
        action="store_true",
        help="Compare every alpha in the registry",
    )
    p_compare.add_argument(
        "--zoo",
        default=None,
        help="Filter comparison to one zoo (e.g. alpha101)",
    )
    p_compare.add_argument(
        "--universe",
        default="csi300",
        choices=_UNIVERSE_CHOICES,
        help=f"Universe (default: csi300; one of {', '.join(_UNIVERSE_CHOICES)})",
    )
    p_compare.add_argument(
        "--period",
        default="2020-2025",
        help="Period spec: YYYY-YYYY or YYYY-MM-DD/YYYY-MM-DD (e.g. 2020-2025)",
    )
    p_compare.add_argument(
        "--sort",
        default="ir",
        choices=list(_COMPARE_SORT_KEYS),
        help=f"Rank by which metric (default: ir; one of {', '.join(_COMPARE_SORT_KEYS)})",
    )

    p_export = alpha_sub.add_parser("export-manifest", help="Export registry manifest as JSON")
    p_export.add_argument("--out", required=True, help="Output JSON path")
    p_export.add_argument("--force", action="store_true", help="Allow writing outside the repo root")

    _ALPHA_PARSER = alpha_parser
    return alpha_parser


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch ``alpha <sub>`` to the matching handler.

    Returns the exit code; ``cli.py`` propagates it via ``_coerce_exit_code``.
    """
    sub = getattr(args, "alpha_command", None)
    if sub is None:
        if _ALPHA_PARSER is not None:
            _ALPHA_PARSER.print_help()
        else:
            _err("alpha requires a subcommand. Try: vibe-trading alpha list")
        return 1
    handler = _DISPATCH.get(sub)
    if handler is None:
        _err(f"alpha: unknown subcommand {sub!r}")
        return 1
    return handler(args)
