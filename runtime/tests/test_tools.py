"""Tool layer tests — file IO sandbox, shell allowlist."""

from pathlib import Path

import pytest

from agency.tools import ToolContext, _read_file, _safe_path, _write_file, _list_dir, _run_shell


def _ctx(tmp_path: Path, *, allow_shell: bool = False) -> ToolContext:
    return ToolContext(workdir=tmp_path.resolve(), allow_shell=allow_shell, allow_network=False)


def test_safe_path_blocks_parent_escape(tmp_path: Path):
    ctx = _ctx(tmp_path)
    with pytest.raises(PermissionError):
        _safe_path(ctx, "../etc/passwd")


def test_write_then_read_roundtrip(tmp_path: Path):
    ctx = _ctx(tmp_path)
    res = _write_file({"path": "hello.txt", "content": "hi"}, ctx)
    assert not res.is_error
    res = _read_file({"path": "hello.txt"}, ctx)
    assert res.content == "hi"


def test_list_dir_shows_entries(tmp_path: Path):
    ctx = _ctx(tmp_path)
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub").mkdir()
    res = _list_dir({"path": "."}, ctx)
    assert "f a.txt" in res.content
    assert "d sub" in res.content


def test_shell_disabled_by_default(tmp_path: Path):
    ctx = _ctx(tmp_path, allow_shell=False)
    res = _run_shell({"command": "ls"}, ctx)
    assert res.is_error
    assert "disabled" in res.content.lower()


def test_shell_allowlist_blocks_unknown_command(tmp_path: Path):
    ctx = _ctx(tmp_path, allow_shell=True)
    res = _run_shell({"command": "rm -rf /"}, ctx)
    assert res.is_error
    assert "allowlist" in res.content.lower()


def test_shell_runs_allowed_command(tmp_path: Path):
    (tmp_path / "marker.txt").write_text("present")
    ctx = _ctx(tmp_path, allow_shell=True)
    res = _run_shell({"command": "ls"}, ctx)
    assert not res.is_error
    assert "marker.txt" in res.content
