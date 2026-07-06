from __future__ import annotations

from rich.console import Console

from cli.ui.banner import print_banner
from cli.ui.rail import RailRunDashboard
from cli.ui.transcript import render_answer, render_elapsed_status, render_prompt_footer, render_recap


def _render(renderable) -> str:
    console = Console(record=True, force_terminal=False, color_system=None, width=100)
    console.print(renderable)
    return console.export_text()


def test_rail_uses_codex_marker_and_output_branch() -> None:
    dash = RailRunDashboard("check price", 50)
    dash.handle_event("tool_call", {"tool": "get_market_data", "arguments": {"symbol": "AAPL"}})
    dash.handle_event(
        "tool_progress",
        {"tool": "get_market_data", "stage": "fetch", "current": 1, "total": 2, "message": "downloaded candles"},
    )
    dash.handle_event("tool_result", {"tool": "get_market_data", "status": "ok", "elapsed_ms": 1200, "preview": "AAPL 195.00"})
    dash.finish({"status": "success", "content": "AAPL is trading near 195.00."}, 1.2)

    out = _render(dash.render())

    assert "• Read market data AAPL" in out
    assert "└  AAPL" in out
    assert "└  fetch · 1/2 · downloaded candles" in out
    assert "•  Done." in out
    assert "●" not in out
    assert "⏺" not in out


def test_rail_renders_codex_style_shell_transcript() -> None:
    dash = RailRunDashboard("show status", 50)
    dash.handle_event(
        "tool_call",
        {
            "tool": "bash",
            "arguments": {"command": "git status --short agent\\cli\\main.py docs\\screenshots\\boot.png"},
        },
    )
    dash.handle_event(
        "tool_result",
        {
            "tool": "bash",
            "status": "ok",
            "elapsed_ms": 200,
            "preview": (
                '{"status":"ok","stdout":"M  CHANGELOG.md\\n M agent/.env.example\\n'
                'M  agent/cli/main.py\\nA  docs/screenshots/boot.png\\n'
                'A  docs/screenshots/agent-run.png\\n","stderr":""}'
            ),
        },
    )

    out = _render(dash.render())

    assert "• Ran git status --short agent\\cli\\main.py docs\\screenshots\\boot.png" in out
    assert "└  M  CHANGELOG.md" in out
    assert "M agent/.env.example" in out
    assert "A  docs/screenshots/boot.png" in out


def test_run_elapsed_is_rendered_as_last_status_line() -> None:
    dash = RailRunDashboard("long command", 50)
    dash.handle_event(
        "tool_call",
        {"tool": "bash", "arguments": {"command": "python slow_task.py"}},
    )
    dash.start_time -= 2.2

    out = _render(dash.render())
    dash.close()

    assert "Running python slow_task.py" in out
    assert "2s" in out
    assert "tokens" not in out
    assert out.rstrip().splitlines()[-1].startswith("· ")


def test_initial_rail_renders_status_line_without_steps() -> None:
    dash = RailRunDashboard("starting", 50)
    dash.start_time -= 1.2

    out = _render(dash.render())
    dash.close()

    assert out.rstrip().startswith("· ")
    assert "1s" in out


def test_banner_renders_large_logo_and_metadata() -> None:
    console = Console(record=True, force_terminal=False, color_system=None, width=100)
    print_banner(console, model="test-model", skills=1, tools=2, sessions=0, version="9.9.9")
    out = console.export_text()

    assert "__      ___ _" in out
    assert "vibe-trading v9.9.9  ·  cli  ·  test-model" in out


def test_transcript_helpers_render_prompt_recap_and_elapsed() -> None:
    recap = render_recap(
        [
            {"role": "user", "content": "check the price of AAPL"},
            {"role": "assistant", "content": "AAPL is trading near $217.61."},
        ]
    )

    assert recap is not None
    assert "※ recap:" in recap.plain
    assert "Last request: check the price of AAPL" in recap.plain
    assert render_elapsed_status(159).plain == "✻ Analyzed for 2m 39s"
    assert render_prompt_footer(width=16).plain == "────────────────"


def test_interactive_result_prints_elapsed_after_answer() -> None:
    from cli.main import _print_interactive_result

    console = Console(record=True, force_terminal=False, color_system=None, width=100)
    _print_interactive_result(
        console,
        {"status": "success", "content": "Final answer text."},
        56,
    )
    out = console.export_text()

    assert out.index("Final answer text.") < out.index("Analyzed for 56s")


def test_answer_renderer_upgrades_markdown_pipe_tables() -> None:
    content = """AAPL snapshot:

| Metric | Value |
|------|------|
| **Last** | **$217.61** |
| Change | -$1.90 (-0.86%) |
"""
    out = _render(render_answer(content))

    assert "$217.61" in out
    assert "Metric" in out
    assert "| **Last** | **$217.61** |" not in out


def test_answer_renderer_strips_standalone_horizontal_rules() -> None:
    """`---` HR lines render as ugly full-width terminal lines — drop them."""
    content = """## Section A

收益指标
- total_return: 15%

---

## Section B

风险指标
- max_drawdown: -8%

***

## Section C

更多内容
"""
    out = _render(render_answer(content))

    assert "Section A" in out
    assert "Section B" in out
    assert "Section C" in out
    # Rich's HR is rendered with U+2500. After stripping `---` / `***`
    # standalone lines, no run of three or more box-drawing chars should
    # appear in the rendered output (table borders are short and bracketed).
    assert "─" * 10 not in out
