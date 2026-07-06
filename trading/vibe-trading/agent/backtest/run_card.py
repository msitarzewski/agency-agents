"""Trust Layer run card generator for backtest runs."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "0.1"
BACKTEST_SUMMARY_KEYS = (
    "codes",
    "start_date",
    "end_date",
    "interval",
    "engine",
    "initial_cash",
    "source",
)


def write_run_card(
    run_dir: Path,
    config: Mapping[str, Any],
    metrics: Mapping[str, Any],
    *,
    data_sources: Sequence[str] | None = None,
    strategy_path: Path | None = None,
    warnings: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Write JSON and Markdown run cards for a backtest run.

    Args:
        run_dir: Directory where run_card.json and run_card.md are written.
        config: Full backtest configuration. Only a summary and hash are stored.
        metrics: Backtest metrics. Scalar values are stored; ``validation`` is
            stored separately when present.
        data_sources: Data sources used by the run.
        strategy_path: Optional strategy source file to hash for reproducibility.
        warnings: Optional warnings to include in the card.

    Returns:
        The run card payload written to ``run_card.json``.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    config_file = run_dir / "config.json"
    reproducibility: dict[str, Any] = {
        "config_hash": _file_hash(config_file) if config_file.exists() else _json_hash(config),
    }
    if strategy_path is not None:
        strategy_file = Path(strategy_path)
        if strategy_file.exists() and strategy_file.is_file():
            reproducibility["strategy_hash"] = _file_hash(strategy_file)

    card: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "run_dir": str(run_dir),
        "backtest": _backtest_summary(config),
        "reproducibility": reproducibility,
        "data_sources": list(data_sources or []),
        "metrics": _scalar_metrics(metrics),
        "warnings": list(warnings or []),
        "artifacts": _list_artifacts(run_dir),
    }
    if "validation" in metrics:
        card["validation"] = metrics["validation"]

    card = _json_safe(card)
    json_path = run_dir / "run_card.json"
    md_path = run_dir / "run_card.md"
    json_path.write_text(
        json.dumps(
            card,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(card), encoding="utf-8")
    return card


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {key: val for key, val in value.items() if not str(key).startswith("_")},
        sort_keys=True,
        default=str,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _backtest_summary(config: Mapping[str, Any]) -> dict[str, Any]:
    return {key: config.get(key) for key in BACKTEST_SUMMARY_KEYS if key in config}


def _scalar_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key != "validation" and _is_scalar(value)
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _list_artifacts(run_dir: Path) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    for relative in (Path("config.json"), Path("code/signal_engine.py")):
        path = run_dir / relative
        if path.exists() and path.is_file():
            candidates.append(path)

    artifacts_dir = run_dir / "artifacts"
    if artifacts_dir.exists() and artifacts_dir.is_dir():
        candidates.extend(path for path in artifacts_dir.rglob("*") if path.is_file())

    artifacts = []
    for path in sorted(candidates, key=lambda item: item.relative_to(run_dir).as_posix()):
        artifacts.append(
            {
                "path": path.relative_to(run_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _file_hash(path),
            }
        )
    return artifacts


def _render_markdown(card: Mapping[str, Any]) -> str:
    lines = [
        "# Backtest Run Card",
        "",
        f"Generated: {card['generated_at']}",
        f"Run directory: `{card['run_dir']}`",
        "",
        "## Backtest Summary",
    ]

    backtest = card.get("backtest", {})
    if backtest:
        lines.extend(f"- {key}: {value}" for key, value in backtest.items())
    else:
        lines.append("- No backtest summary fields provided.")

    lines.extend(["", "## Reproducibility"])
    reproducibility = card.get("reproducibility", {})
    lines.append(f"- config_hash: `{reproducibility.get('config_hash', '')}`")
    if "strategy_hash" in reproducibility:
        lines.append(f"- strategy_hash: `{reproducibility['strategy_hash']}`")

    lines.extend(["", "## Data Sources"])
    data_sources = card.get("data_sources", [])
    lines.extend(f"- {source}" for source in data_sources) if data_sources else lines.append("- None recorded.")

    lines.extend(["", "## Metrics"])
    metric_values = card.get("metrics", {})
    lines.extend(f"- {key}: {value}" for key, value in metric_values.items()) if metric_values else lines.append("- No scalar metrics recorded.")

    lines.extend(["", "## Validation"])
    if "validation" in card:
        validation = card["validation"]
        if isinstance(validation, Mapping):
            lines.extend(f"- {key}: {value}" for key, value in validation.items())
        else:
            lines.append(f"- {validation}")
    else:
        lines.append("- Not present.")

    warnings = card.get("warnings", [])
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend(["", "## Artifacts"])
    artifacts = card.get("artifacts", [])
    if artifacts:
        lines.extend(
            f"- `{artifact['path']}` ({artifact['size_bytes']} bytes, sha256 `{artifact['sha256']}`)"
            for artifact in artifacts
        )
    else:
        lines.append("- None found.")

    return "\n".join(lines) + "\n"
