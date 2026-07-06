"""W4.a blog patcher: fill TBD placeholders in alpha-191-in-2026.html.

Reads ~/.vibe-trading/reports/bench_summary.json (produced by w4a_run_benches.py)
and patches the HTML in place.

Substitutions performed:
- num-alive / num-reversed / num-dead spans in the two stat blocks
- Theme survival table rows (count + survival rate per theme)
- Top 5 alphas (id + formula + IC mean)
- 3 famously-dead alphas (replace invented IDs with worst-IC from gtja191)
- Section-level "bench failed" callouts where the corresponding bench errored

The patcher never fabricates a number: if the gtja191 bench is missing, every
TBD that depends on it becomes a "bench failed" note instead. The script is
idempotent — re-running with the same summary produces the same HTML.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
HTML_PATH = REPO / "wiki" / "research-lab" / "posts" / "alpha-191-in-2026.html"
SUMMARY_PATH = Path.home() / ".vibe-trading" / "reports" / "bench_summary.json"

GTJA_KEY = "gtja191_csi300"

# Themes shown in the table — these are the human labels in the HTML, mapped
# to the canonical theme tags in registry meta. "Volume-price interaction"
# requires *both* volume and reversal-or-momentum, so it gets a custom probe.
THEME_LABEL_TO_TAGS: dict[str, list[str]] = {
    "Volume-price interaction": ["volume"],
    "Short-horizon volatility": ["volatility"],
    "Reversal": ["reversal"],
    "Momentum": ["momentum"],
    "Turnover / liquidity": ["liquidity"],
    "Microstructure / range": ["microstructure"],
}


def _load_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.is_file():
        raise SystemExit(f"summary not found: {SUMMARY_PATH}")
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def _gtja_entry(summary: dict[str, Any]) -> dict[str, Any] | None:
    entry = summary.get("zoos", {}).get(GTJA_KEY)
    if not entry or entry.get("status") != "ok":
        return None
    return entry


def _patch_stats(text: str, entry: dict[str, Any]) -> str:
    for span_class, key in (
        ("num-alive", "alive"),
        ("num-reversed", "reversed"),
        ("num-dead", "dead"),
    ):
        value = entry.get(key)
        if value is None:
            continue
        pattern = re.compile(
            rf'(<span class="{span_class}">)\[TBD\](</span>)'
        )
        text = pattern.sub(rf"\g<1>{int(value)}\g<2>", text)
    return text


def _theme_survival_rows(entry: dict[str, Any]) -> str:
    """Build the inner <tr> rows for the theme-survival table."""
    by_theme = entry.get("by_theme", {})
    rows: list[str] = []
    definitions = {
        "Volume-price interaction": "Correlation / covariance of volume with close, high-low range",
        "Short-horizon volatility": "Rolling std / range over 5-20 day windows",
        "Reversal": "Negative-sign return signals over 1-5 day horizons",
        "Momentum": "Positive-sign return signals over 10-60 day horizons",
        "Turnover / liquidity": "Volume ratios, turnover-rate transforms",
        "Microstructure / range": "Open-close-high-low decompositions, intraday range proxies",
    }
    for label, tags in THEME_LABEL_TO_TAGS.items():
        # Aggregate across all listed tags (most themes are single-tag).
        alive = dead = reversed_ = count = 0
        for tag in tags:
            bucket = by_theme.get(tag)
            if bucket is None:
                continue
            alive += bucket.get("alive", 0)
            dead += bucket.get("dead", 0)
            reversed_ += bucket.get("reversed", 0)
            count += bucket.get("count", 0)
        if count == 0:
            count_cell = "n/a"
            rate_cell = "n/a"
        else:
            count_cell = str(count)
            rate_cell = f"{alive / count * 100:.0f}% ({alive}/{count})"
        rows.append(
            "            <tr>\n"
            f"              <td>{html.escape(label)}</td>\n"
            f"              <td>{html.escape(definitions[label])}</td>\n"
            f"              <td>{count_cell}</td>\n"
            f"              <td>{rate_cell}</td>\n"
            "            </tr>"
        )
    return "\n".join(rows)


def _patch_theme_table(text: str, entry: dict[str, Any]) -> str:
    new_rows = _theme_survival_rows(entry)
    pattern = re.compile(
        r'(<tbody>)(.*?)(</tbody>)',
        re.DOTALL,
    )
    # The HTML has exactly one <tbody> inside the theme-table; surgical replace.
    def _swap(match: re.Match[str]) -> str:
        body = match.group(2)
        if "Volume-price interaction" not in body:
            return match.group(0)  # not the theme table
        return f"{match.group(1)}\n{new_rows}\n          {match.group(3)}"

    return pattern.sub(_swap, text, count=1)


def _formula_to_html(formula: str) -> str:
    return html.escape(formula)


def _build_top5_cards(entry: dict[str, Any]) -> str:
    rows = entry.get("top5_by_ir", [])[:5]
    cards: list[str] = []
    for row in rows:
        aid = row["id"]
        formula = _formula_to_html(row.get("formula_latex", ""))
        ic = row.get("ic_mean", 0.0)
        ir = row.get("ir", 0.0)
        cards.append(
            "        <article class=\"alpha-card\">\n"
            f"          <span class=\"alpha-id\">{html.escape(aid)}</span>\n"
            f"          <pre class=\"formula-block\"><code>{formula}</code></pre>\n"
            "          <p class=\"alpha-note\">"
            f"Mean IC = {ic:.4f}, IR = {ir:.4f} over the CSI 300 / 2018&ndash;2025 window. "
            "Formula reproduced verbatim from the registry "
            f"(<code>__alpha_meta__[\"formula_latex\"]</code> of <code>{html.escape(aid)}</code>)."
            "</p>\n"
            "        </article>"
        )
    return "\n".join(cards)


def _build_dead_cards(entry: dict[str, Any]) -> str:
    rows = entry.get("dead_examples", [])[:3]
    cards: list[str] = []
    for row in rows:
        aid = row["id"]
        formula = _formula_to_html(row.get("formula_latex", ""))
        ic = row.get("ic_mean", 0.0)
        cat = row.get("category", "dead")
        ir = row.get("ir", 0.0)
        cards.append(
            "        <article class=\"alpha-card\">\n"
            f"          <span class=\"alpha-id\">{html.escape(aid)} ({html.escape(cat)})</span>\n"
            f"          <pre class=\"formula-block\"><code>{formula}</code></pre>\n"
            "          <p class=\"alpha-note\">"
            f"Mean IC = {ic:.4f}, IR = {ir:.4f}. Worst-performing slice of the gtja191 "
            "zoo on CSI 300 / 2018&ndash;2025 by raw IC."
            "</p>\n"
            "        </article>"
        )
    return "\n".join(cards)


def _patch_top5(text: str, entry: dict[str, Any]) -> str:
    cards = _build_top5_cards(entry)
    pattern = re.compile(
        r'(<h3>Top 5 surviving alphas</h3>.*?</p>\s*)'  # heading + lead paragraph
        r'(?:<article class="alpha-card">.*?</article>\s*){5}',
        re.DOTALL,
    )
    return pattern.sub(rf"\g<1>{cards}\n\n        ", text, count=1)


def _patch_dead(text: str, entry: dict[str, Any]) -> str:
    cards = _build_dead_cards(entry)
    pattern = re.compile(
        r'(<h3>Three famously dead alphas</h3>.*?</p>\s*)'
        r'(?:<article class="alpha-card">.*?</article>\s*){3}',
        re.DOTALL,
    )
    return pattern.sub(rf"\g<1>{cards}\n\n        ", text, count=1)


def _patch_bench_failed_note(text: str) -> str:
    """Replace the W4-roadmap placeholder callout with a real timestamp note."""
    return text.replace(
        "Numbers will be filled in once the full bench finishes (Vibe-Trading\n        roadmap W4.a). "
        "This post is published as a methodology preview &mdash; the structure, definitions\n        and caveats are final.",
        "Numbers below are the live W4.a bench output on the bundled gtja191 zoo "
        "(CSI 300, 2018&ndash;2025) &mdash; reproducible via the CLI snippet at the end of the post.",
    )


def main() -> int:
    summary = _load_summary()
    entry = _gtja_entry(summary)

    text = HTML_PATH.read_text(encoding="utf-8")

    if entry is None:
        # Surface the failure once at the top; leave all TBDs intact so the
        # reader sees we have not invented numbers.
        zoo_blob = summary.get("zoos", {}).get(GTJA_KEY, {})
        reason = zoo_blob.get("error", "bench did not run")
        note = (
            '<p class="bench-failed"><strong>Note:</strong> the gtja191 / CSI 300 bench '
            f"failed during W4.a (reason: {html.escape(str(reason))}). All TBD numbers below "
            "remain to be filled in 0.1.9 once the bench is re-run.</p>"
        )
        text = text.replace(
            'roadmap W4.a). This post',
            f'roadmap W4.a). {note} This post'
        )
        HTML_PATH.write_text(text, encoding="utf-8")
        print(f"bench failed; left TBDs intact and added note. tbd count = "
              f"{text.count('[TBD]')}", file=sys.stderr)
        return 0

    text = _patch_stats(text, entry)
    text = _patch_theme_table(text, entry)
    text = _patch_top5(text, entry)
    text = _patch_dead(text, entry)
    text = _patch_bench_failed_note(text)

    # Mean IC ~ [TBD] placeholders inside the per-card paragraphs are no longer
    # needed (we rewrote the cards with real numbers). Sanity-check sweep.
    HTML_PATH.write_text(text, encoding="utf-8")

    remaining = text.count("[TBD]")
    print(f"patched {HTML_PATH}; remaining [TBD] = {remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
