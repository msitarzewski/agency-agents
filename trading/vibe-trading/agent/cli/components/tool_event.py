"""Single tool invocation render.

Layout (matches design_proposal §3.5):

    ● Get Financials ("AAPL", quarterly, last 8 quarters)         1.4s · 8 quarters

* ``●`` (U+25CF black circle) marker, color-coded by status:
    running → ``--warning`` amber (pulse via Rich style ``blink`` when
              the terminal advertises it, otherwise solid amber)
    ok      → ``--success`` green, solid
    error   → ``--danger`` red, solid
* Tool name pretty-printed (``get_financials`` → ``Get Financials``)
* Args summary prefers ``query`` then ``prompt``, else the first 2
  ``key=value`` pairs each truncated to 40 chars
* Duration formatted via :func:`agent.cli.utils.format.format_duration`
  when Parcel α has shipped it; otherwise a local fallback is used
"""

from __future__ import annotations

from typing import Any, Iterable, Literal, Mapping

from rich.text import Text


Status = Literal["running", "ok", "error"]


# Status → (Rich style, marker glyph). The glyph stays the same; the style
# encodes color + decoration (bold/blink). dexter only changes brightness
# of the marker rather than swapping glyphs.
_STATUS_STYLE: dict[Status, str] = {
    # ``blink`` is gracefully ignored by Rich when the terminal does not
    # advertise the capability, so we always include it.
    "running": "bold blink #f59e0b",   # amber, F-002 warning
    "ok":      "bold #16a34a",          # green, F-002 success
    "error":   "bold #dc2626",          # red, F-002 danger
}

_ARG_VALUE_MAX = 40


# ---------------------------------------------------------------- helpers ----


def _pretty_tool_name(name: str) -> str:
    """Convert ``get_financials`` to ``Get Financials``.

    Strips a leading ``get_`` prefix when present (dexter convention).
    Underscores and hyphens become spaces; each whitespace-separated
    token is title-cased. Acronyms preserved when fully upper.
    """
    cleaned = name.strip()
    if cleaned.lower().startswith("get_"):
        cleaned = cleaned[4:]
    tokens = cleaned.replace("-", " ").replace("_", " ").split()
    out: list[str] = []
    for tok in tokens:
        if tok.isupper() and len(tok) <= 4:
            out.append(tok)
        else:
            out.append(tok[:1].upper() + tok[1:].lower())
    return " ".join(out) if out else cleaned


def _truncate(value: str, limit: int = _ARG_VALUE_MAX) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _summarize_args(args: Mapping[str, Any] | None) -> str:
    """Produce a one-line args summary.

    Rules:
        * ``args is None`` or empty → empty string
        * ``query`` field present → ``"<value>"`` (quoted)
        * ``prompt`` field present → ``"<value>"`` (quoted)
        * otherwise → first 2 ``key=value`` pairs, value truncated to 40 chars

    Returns the bare summary string; callers wrap it in parens.
    """
    if not args:
        return ""

    # Prefer the well-known semantic keys
    for primary_key in ("query", "prompt"):
        if primary_key in args:
            return f'"{_truncate(str(args[primary_key]))}"'

    pairs: list[str] = []
    for key, value in list(args.items())[:2]:
        rendered_value = _truncate(_render_value(value))
        pairs.append(f"{key}={rendered_value}")
    return ", ".join(pairs)


def _render_value(value: Any) -> str:
    """Compact ``repr``-ish formatting suitable for inline arg display."""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (list, tuple)):
        # Show length to avoid blowing up the line on huge arrays.
        if len(value) <= 3:
            return "[" + ", ".join(_render_value(v) for v in value) + "]"
        return f"[{len(value)} items]"
    if isinstance(value, Mapping):
        return f"{{{len(value)} keys}}"
    return str(value)


def _format_duration_local(ms: float) -> str:
    """Local fallback when ``agent.cli.utils.format.format_duration`` is absent.

    Parcel α owns the canonical implementation; until it lands we keep a
    minimal version here so the demo build is not blocked on cross-parcel
    ordering. Numbers match the contract in design_proposal §3.5:

        < 1000ms   → "740ms"
        < 60s      → "1.4s"
        ≥ 60s      → "1m12s"
    """
    if ms < 1000:
        return f"{int(round(ms))}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    rem = int(seconds - minutes * 60)
    return f"{minutes}m{rem:02d}s"


def _format_duration(ms: float) -> str:
    """Delegate to the shared formatter; fall back locally on import error."""
    try:
        from cli.utils.format import format_duration

        return format_duration(ms)
    except Exception:  # noqa: BLE001 — never block render on helper issues
        return _format_duration_local(ms)


# ---------------------------------------------------------------- public ----


def render_tool_event(
    name: str,
    args: Mapping[str, Any] | None = None,
    status: Status = "running",
    duration_ms: float | None = None,
    *,
    result_summary: str | None = None,
) -> Text:
    """Return a Rich :class:`Text` row describing a single tool call.

    Args:
        name: Raw tool name (``get_financials``); pretty-printed in output.
        args: Argument mapping; summarised inline.
        status: ``"running"`` | ``"ok"`` | ``"error"``.
        duration_ms: When the call finished, total wall time in milliseconds.
        result_summary: Optional one-line summary appended after the
            duration (e.g. ``"8 quarters"``).

    Returns:
        A Rich ``Text`` object — caller decides whether to ``console.print``
        it, stuff it into a ``Group``, or stream it as a transient row.
    """
    if status not in _STATUS_STYLE:
        # Be lenient — unknown statuses degrade to "running" instead of
        # raising; CLI rendering should never crash the agent loop.
        status = "running"

    marker = Text("● ", style=_STATUS_STYLE[status])
    line = Text()
    line.append(marker)
    line.append(_pretty_tool_name(name), style="bold")

    summary = _summarize_args(args)
    if summary:
        line.append(f" ({summary})", style="dim")

    suffix_parts: list[str] = []
    if duration_ms is not None:
        suffix_parts.append(_format_duration(duration_ms))
    if result_summary:
        suffix_parts.append(result_summary)
    if suffix_parts:
        line.append("   " + " · ".join(suffix_parts), style="dim")

    return line


def render_tool_events(events: Iterable[Mapping[str, Any]]) -> list[Text]:
    """Convenience: render a list of event dicts.

    Each event dict needs ``name`` plus any of ``args`` / ``status`` /
    ``duration_ms`` / ``result_summary``. Useful for replaying a stored
    run via :mod:`agent.cli.commands.show`.
    """
    rendered: list[Text] = []
    for ev in events:
        rendered.append(
            render_tool_event(
                name=str(ev.get("name", "tool")),
                args=ev.get("args"),
                status=ev.get("status", "ok"),
                duration_ms=ev.get("duration_ms"),
                result_summary=ev.get("result_summary"),
            )
        )
    return rendered


__all__ = ["render_tool_event", "render_tool_events"]
