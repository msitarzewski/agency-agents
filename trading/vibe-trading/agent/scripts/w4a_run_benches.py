"""W4.a bench driver: run 4 zoo×universe combinations and emit summary JSON.

Usage:
    cd agent && python scripts/w4a_run_benches.py

Output:
    ~/.vibe-trading/reports/alpha_bench_*.html      — per-run HTML reports
    ~/.vibe-trading/reports/bench_<zoo>_<uni>.json  — per-run raw results
    ~/.vibe-trading/reports/bench_summary.json      — aggregate summary

Safe to re-run; each bench result is cached by ``_load_universe_panel`` so the
expensive Tushare/yfinance fetches only happen once per (universe, period).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Repo-relative imports
HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
sys.path.insert(0, str(AGENT_DIR))

load_dotenv(AGENT_DIR / ".env")

# Configure logging early so universe loaders log their progress.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("w4a")

from src.factors.bench_runner import run_bench  # noqa: E402
from src.tools.alpha_bench_tool import run_alpha_bench  # noqa: E402


REPORTS_DIR = Path.home() / ".vibe-trading" / "reports"

BENCHES = [
    {"key": "gtja191_csi300", "zoo": "gtja191", "universe": "csi300", "period": "2018-2025"},
    {"key": "alpha101_sp500", "zoo": "alpha101", "universe": "sp500", "period": "2020-2025"},
    {"key": "qlib158_csi300", "zoo": "qlib158", "universe": "csi300", "period": "2020-2025"},
    {"key": "alpha101_btc", "zoo": "alpha101", "universe": "btc-usdt", "period": "2022-2025"},
]


def _run_one(bench: dict) -> dict:
    """Run a single bench end-to-end. Returns a summary entry.

    Delegates the math to ``src.factors.bench_runner.run_bench``; this wrapper
    just adds the HTML report (via ``run_alpha_bench``) and persists the raw
    per-alpha rows for downstream tooling, both of which the CLI driver wants
    but the API route does not.
    """
    key = bench["key"]
    zoo = bench["zoo"]
    universe = bench["universe"]
    period = bench["period"]
    logger.info("=== bench %s: zoo=%s universe=%s period=%s ===", key, zoo, universe, period)
    start = time.monotonic()

    entry: dict = {
        "key": key,
        "zoo": zoo,
        "universe": universe,
        "period": period,
        "status": "pending",
    }

    # 1. HTML report (also exercises the universe loader so the panel is cached
    #    on disk for the run_bench call below).
    try:
        envelope = run_alpha_bench(
            zoo=zoo, universe=universe, period=period, top=20
        )
    except Exception as exc:  # noqa: BLE001 — never let one bench abort the suite
        logger.exception("bench %s crashed (run_alpha_bench)", key)
        entry["status"] = "error"
        entry["error"] = f"unexpected: {exc!s}"
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    if envelope.get("status") != "ok":
        entry["status"] = "error"
        entry["error"] = envelope.get("error", "unknown")
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    # 2. Full bench (per-alpha rows + categorisation).
    try:
        result = run_bench(zoo=zoo, universe=universe, period=period, top=20)
    except Exception as exc:  # noqa: BLE001
        logger.exception("bench %s crashed (run_bench)", key)
        entry["status"] = "error"
        entry["error"] = f"unexpected: {exc!s}"
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    if result.get("status") != "ok":
        entry["status"] = "error"
        entry["error"] = result.get("error", "unknown")
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    rows = result.pop("rows", [])
    skipped = result.pop("skipped", [])

    entry.update(result)
    entry["report_path"] = envelope.get("report_path")
    entry["wall_seconds"] = round(time.monotonic() - start, 2)

    # Write per-bench raw rows for downstream tooling.
    raw_path = REPORTS_DIR / f"bench_{key}.json"
    raw_path.write_text(
        json.dumps(
            {"meta": {k: entry[k] for k in ("key", "zoo", "universe", "period", "status")},
             "rows": rows, "skipped": skipped},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    logger.info(
        "bench %s done: tested=%d skipped=%d alive=%d reversed=%d dead=%d (%.1fs)",
        key, len(rows), len(skipped),
        entry["alive"], entry["reversed"], entry["dead"],
        entry["wall_seconds"],
    )
    return entry


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zoos": {},
    }

    tushare_ok = bool(os.getenv("TUSHARE_TOKEN", "").strip())
    if not tushare_ok:
        logger.warning("TUSHARE_TOKEN unset; csi300 benches will be skipped")

    for bench in BENCHES:
        if bench["universe"] == "csi300" and not tushare_ok:
            summary["zoos"][bench["key"]] = {
                **{k: bench[k] for k in ("zoo", "universe", "period")},
                "status": "skipped",
                "error": "TUSHARE_TOKEN not set",
            }
            continue
        entry = _run_one(bench)
        summary["zoos"][bench["key"]] = entry

    out = REPORTS_DIR / "bench_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    logger.info("wrote summary -> %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
