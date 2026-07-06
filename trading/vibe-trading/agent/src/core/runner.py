"""Runner module for executing generated backtest code and collecting artifacts."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console


console = Console(stderr=True)


@dataclass
class RunResult:
    """Container for runner execution outputs.

    Attributes:
        success: Whether subprocess exited with code 0.
        exit_code: Subprocess return code.
        stdout: Captured stdout text.
        stderr: Captured stderr text.
        artifacts: Existing artifact file paths keyed by artifact name.
    """

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    artifacts: dict[str, Path]


_ARTIFACTS_SPEC = {
    "defaults": {"required": ["equity", "metrics", "trades"]},
    "schemas": {
        "equity_csv": {
            "columns": [
                {"name": "timestamp", "type": "string"},
                {"name": "ret", "type": "float"},
                {"name": "equity", "type": "float"},
                {"name": "drawdown", "type": "float"},
            ],
        },
        "metrics_csv": {
            "columns": [
                {"name": "final_value", "type": "float"},
                {"name": "total_return", "type": "float"},
                {"name": "annual_return", "type": "float"},
                {"name": "max_drawdown", "type": "float"},
                {"name": "sharpe", "type": "float"},
                {"name": "win_rate", "type": "float"},
                {"name": "trade_count", "type": "integer"},
            ],
        },
        "trade_log": {
            "columns": [
                {"name": "timestamp", "type": "string"},
                {"name": "code", "type": "string"},
                {"name": "side", "type": "string"},
                {"name": "price", "type": "float"},
                {"name": "qty", "type": "float"},
                {"name": "reason", "type": "string"},
            ],
        },
    },
    "artifacts": {
        "equity": {"schema": "equity_csv", "path": "artifacts/equity.csv"},
        "metrics": {"schema": "metrics_csv", "path": "artifacts/metrics.csv"},
        "trades": {"schema": "trade_log", "path": "artifacts/trades.csv"},
        "positions": {"schema": "positions_csv", "path": "artifacts/positions.csv"},
        "run_card_json": {"schema": "json", "path": "run_card.json"},
        "run_card_md": {"schema": "markdown", "path": "run_card.md"},
    },
}


def _expand_artifacts_spec(spec: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    """Expand artifacts_spec into a name -> metadata dict.

    Args:
        spec: Raw artifact spec.

    Returns:
        Expanded artifact metadata mapping.
    """
    if not isinstance(spec, dict):
        return {}
    schemas = spec.get("schemas") or {}
    artifacts = spec.get("artifacts") or {}
    defaults = spec.get("defaults") or {}
    required = set(defaults.get("required") or [])
    expanded: Dict[str, Dict[str, Any]] = {}
    for name, meta in artifacts.items():
        if not isinstance(meta, dict):
            continue
        schema_name = meta.get("schema")
        schema = schemas.get(schema_name, {}) if isinstance(schemas, dict) else {}
        expanded[name] = {
            "path": meta.get("path"),
            "required": bool(meta.get("required", name in required)),
            "columns": meta.get("columns") or schema.get("columns"),
        }
    return expanded


class Runner:
    """Execute entry scripts inside a run directory and collect outputs."""

    def __init__(self, timeout: int = 300, artifacts_spec: Optional[Dict[str, Any]] = None) -> None:
        """Initialize runner.

        Args:
            timeout: Max subprocess runtime in seconds.
            artifacts_spec: Artifact spec from config.
        """

        self.timeout = timeout
        self.artifacts_spec = artifacts_spec or _ARTIFACTS_SPEC
        self.artifact_entries = _expand_artifacts_spec(self.artifacts_spec)

    def _python_ready(self, python_cmd: str) -> bool:
        """Check whether a Python interpreter can import runtime dependencies.

        Args:
            python_cmd: Interpreter executable path.

        Returns:
            True if required imports succeed, otherwise False.
        """

        try:
            probe = subprocess.run(
                [python_cmd, "-c", "import pandas,numpy; print('ok')"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
            return probe.returncode == 0
        except Exception:
            return False

    def _pick_python_interpreter(self) -> str:
        """Pick the first usable interpreter for backtest execution.

        Returns:
            Interpreter command path.
        """

        project_root = Path(__file__).resolve().parents[2]
        candidates = [
            project_root / ".venv" / "Scripts" / "python.exe",
            project_root / ".venv" / "bin" / "python",
            Path(sys.executable),
        ]
        for path in candidates:
            if not path.exists():
                continue
            cmd = str(path)
            if self._python_ready(cmd):
                return cmd
        return sys.executable

    def _build_runtime_env(self, run_dir: Path, *, pythonpath_extra: Path | None = None) -> dict[str, str]:
        """Build subprocess env and enforce no-proxy execution.

        Args:
            run_dir: Current run directory.
            pythonpath_extra: Additional path to prepend to PYTHONPATH.

        Returns:
            Environment mapping for subprocess.
        """

        env = os.environ.copy()
        env.update(
            {
                "PYTHONUNBUFFERED": "1",
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
        )

        if pythonpath_extra:
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = str(pythonpath_extra) + (os.pathsep + existing if existing else "")

        # Preserve system proxy settings; data sources (OKX/yfinance) need network access
        # NOTE: do NOT override HOME/USERPROFILE — data libraries (yfinance, akshare)
        # cache downloads under ~/; overriding HOME causes full re-download every run.

        return env

    def execute(
        self,
        entry_script: Path,
        run_dir: Path,
        *,
        cwd: Path | None = None,
        cli_args: list[str] | None = None,
    ) -> RunResult:
        """Run entry script and collect logs and artifacts.

        Args:
            entry_script: Entry script path.
            run_dir: Current run directory.
            cwd: Working directory for subprocess (default: entry_script.parent).
            cli_args: Additional CLI arguments appended to subprocess command.

        Returns:
            RunResult object with process output and discovered artifacts.
        """

        console.print(f"[blue]Runner: executing {entry_script}[/blue]")
        stdout_path = run_dir / "logs" / "runner_stdout.txt"
        stderr_path = run_dir / "logs" / "runner_stderr.txt"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        console.print("[dim]Runner: starting backtest subprocess...[/dim]")

        effective_cwd = cwd or entry_script.parent
        pythonpath_extra = cwd if cwd else None
        env = self._build_runtime_env(run_dir, pythonpath_extra=pythonpath_extra)
        python_cmd = self._pick_python_interpreter()
        console.print(f"[dim]Runner: using Python: {python_cmd}[/dim]")

        cmd = [python_cmd, str(entry_script)]
        if cli_args:
            cmd.extend(cli_args)

        process = subprocess.run(
            cmd,
            cwd=str(effective_cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout,
            env=env,
            encoding="utf-8",
            errors="ignore",
        )

        elapsed = time.time() - start_time
        console.print(f"[blue]Runner: subprocess finished in {elapsed:.2f}s[/blue]")

        stdout_path.write_text(process.stdout, encoding="utf-8")
        stderr_path.write_text(process.stderr, encoding="utf-8")

        if process.stdout:
            console.print(f"[dim]Runner stdout:[/dim]\n{process.stdout}")
        if process.stderr:
            console.print(f"[red]Runner stderr:[/red]\n{process.stderr}")

        artifacts: dict[str, Path] = {}
        for name, info in self.artifact_entries.items():
            rel_path = info.get("path")
            if not isinstance(rel_path, str) or not rel_path.strip():
                continue
            target = run_dir / Path(rel_path)
            if target.exists():
                artifacts[name] = target

        success = process.returncode == 0
        return RunResult(
            success=success,
            exit_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            artifacts=artifacts,
        )
