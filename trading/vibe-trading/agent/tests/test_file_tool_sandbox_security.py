"""Security regression tests for run_dir-based file tools."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from src.tools.backtest_tool import run_backtest
from src.tools.edit_file_tool import EditFileTool
from src.tools.read_file_tool import ReadFileTool
from src.tools.write_file_tool import WriteFileTool
from src.tools.path_utils import allowed_write_roots, resolve_safe_path


def _body(raw: str) -> dict:
    """Parse a JSON tool response."""
    return json.loads(raw)


def test_write_file_rejects_unconfigured_absolute_run_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", raising=False)

    body = _body(WriteFileTool().execute(
        path="code/signal_engine.py",
        content="print('nope')",
        run_dir=str(tmp_path),
    ))

    assert body["status"] == "error"
    assert "outside allowed run roots" in body["error"]
    assert not (tmp_path / "code" / "signal_engine.py").exists()


def test_read_and_edit_file_accept_configured_run_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))
    target = tmp_path / "run" / "notes.md"
    target.parent.mkdir(parents=True)
    target.write_text("alpha beta", encoding="utf-8")

    read_body = _body(ReadFileTool().execute(path="notes.md", run_dir=str(target.parent)))
    edit_body = _body(EditFileTool().execute(
        path="notes.md",
        old_text="beta",
        new_text="gamma",
        run_dir=str(target.parent),
    ))

    assert read_body["status"] == "ok"
    assert "alpha beta" in read_body["content"]
    assert edit_body["status"] == "ok"
    assert target.read_text(encoding="utf-8") == "alpha gamma"


def test_backtest_rejects_unconfigured_absolute_run_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", raising=False)
    (tmp_path / "code").mkdir()
    (tmp_path / "config.json").write_text('{"source":"auto","codes":["AAPL"]}', encoding="utf-8")
    (tmp_path / "code" / "signal_engine.py").write_text(
        "class SignalEngine:\n    def generate(self, data_map):\n        return {}\n",
        encoding="utf-8",
    )

    body = _body(run_backtest(str(tmp_path)))

    assert body["status"] == "error"
    assert "outside allowed run roots" in body["error"]


def test_tilde_expansion_resolves_to_mock_home(tmp_path: Path, monkeypatch) -> None:
    # Mock user home directory
    mock_home = tmp_path / "home_user"
    mock_home.mkdir()
    monkeypatch.setenv("HOME", str(mock_home))
    monkeypatch.setenv("USERPROFILE", str(mock_home))

    # Configure mock home as allowed write root
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_WRITE_ROOTS", str(mock_home / ".vibe-trading"))
    allowed_write = allowed_write_roots()
    assert any(p.is_relative_to(mock_home) for p in allowed_write)

    # Resolve safe path using tilde
    resolved = resolve_safe_path("~/.vibe-trading/scripts/strat.py", None, allowed_write, purpose="write")
    assert resolved == mock_home / ".vibe-trading" / "scripts" / "strat.py"


def test_read_write_separation_prevent_cross_escalation(tmp_path: Path, monkeypatch) -> None:
    read_only_dir = tmp_path / "read_only"
    write_only_dir = tmp_path / "write_only"
    read_only_dir.mkdir()
    write_only_dir.mkdir()

    # Configure separate environment variables
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(read_only_dir))
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_WRITE_ROOTS", str(write_only_dir))

    # Setup read-only file
    ro_file = read_only_dir / "conf.json"
    ro_file.write_text('{"key": "val"}', encoding="utf-8")

    # 1. Read should succeed on read-only root
    read_res = _body(ReadFileTool().execute(path=str(ro_file)))
    assert read_res["status"] == "ok"
    assert "val" in read_res["content"]

    # 2. Write/Edit should FAIL on read-only root (write isolation)
    write_res = _body(WriteFileTool().execute(path=str(ro_file), content="poison"))
    assert write_res["status"] == "error"
    assert "run_dir is required" in write_res["error"] or "escapes" in write_res["error"]
    assert ro_file.read_text(encoding="utf-8") == '{"key": "val"}' # Intact

    # 3. Write should succeed on write-only root
    wo_file = write_only_dir / "output.txt"
    write_ok = _body(WriteFileTool().execute(path=str(wo_file), content="success_write"))
    assert write_ok["status"] == "ok"
    assert wo_file.read_text(encoding="utf-8") == "success_write"


def test_resolve_safe_path_run_dir_escapes_fallback(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "runs" / "run_1"
    run_dir.mkdir(parents=True)
    extra_write_dir = tmp_path / "extra_write"
    extra_write_dir.mkdir()

    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path / "runs"))
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_WRITE_ROOTS", str(extra_write_dir))

    # 1. Inside run_dir -> resolves to run_dir
    resolved_1 = resolve_safe_path("script.py", str(run_dir), allowed_write_roots(), purpose="write")
    assert resolved_1 == run_dir / "script.py"

    # 2. Escapes run_dir but inside extra_write -> resolves to extra_write (fallback)
    resolved_2 = resolve_safe_path(str(extra_write_dir / "tool.py"), str(run_dir), allowed_write_roots(), purpose="write")
    assert resolved_2 == extra_write_dir / "tool.py"

    # 3. Escapes run_dir and not in extra_write -> raises ValueError
    with pytest.raises(ValueError) as excinfo:
        resolve_safe_path("/etc/passwd", str(run_dir), allowed_write_roots(), purpose="write")
    assert "escapes run_dir" in str(excinfo.value)
