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


# ----- plan tool ---------------------------------------------------------


from agency.tools import _plan_tool


def _plan_ctx(tmp_path: Path, session_id: str | None = "s-1") -> ToolContext:
    ctx = _ctx(tmp_path)
    setattr(ctx, "_plan_root", tmp_path / "plans")
    setattr(ctx, "_plan_session_id", session_id)
    return ctx


def test_plan_requires_session(tmp_path: Path):
    ctx = _plan_ctx(tmp_path, session_id=None)
    res = _plan_tool({"action": "view"}, ctx)
    assert res.is_error
    assert "session" in res.content.lower()


def test_plan_view_empty(tmp_path: Path):
    ctx = _plan_ctx(tmp_path)
    res = _plan_tool({"action": "view"}, ctx)
    assert not res.is_error
    assert "no plan yet" in res.content.lower()


def test_plan_write_view_append_clear(tmp_path: Path):
    ctx = _plan_ctx(tmp_path)

    w = _plan_tool({"action": "write", "content": "# Plan\n- [ ] step 1\n"}, ctx)
    assert not w.is_error

    v = _plan_tool({"action": "view"}, ctx)
    assert "# Plan" in v.content
    assert "- [ ] step 1" in v.content

    a = _plan_tool({"action": "append", "content": "- [ ] step 2"}, ctx)
    assert not a.is_error

    v2 = _plan_tool({"action": "view"}, ctx)
    assert "step 2" in v2.content

    c = _plan_tool({"action": "clear"}, ctx)
    assert not c.is_error
    v3 = _plan_tool({"action": "view"}, ctx)
    assert "no plan yet" in v3.content.lower()


def test_plan_rejects_unknown_action(tmp_path: Path):
    ctx = _plan_ctx(tmp_path)
    res = _plan_tool({"action": "nonsense"}, ctx)
    assert res.is_error
    assert "unknown action" in res.content.lower()


def test_plan_scopes_per_session(tmp_path: Path):
    ctx_a = _plan_ctx(tmp_path, session_id="sess-a")
    ctx_b = _plan_ctx(tmp_path, session_id="sess-b")

    _plan_tool({"action": "write", "content": "A's plan"}, ctx_a)
    _plan_tool({"action": "write", "content": "B's plan"}, ctx_b)

    assert "A's plan" in _plan_tool({"action": "view"}, ctx_a).content
    assert "B's plan" in _plan_tool({"action": "view"}, ctx_b).content
