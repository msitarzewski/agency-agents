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


# ----- edit_file ---------------------------------------------------------


from agency.tools import _edit_file, _extract_doc


def test_edit_file_replaces_unique_occurrence(tmp_path: Path):
    ctx = _ctx(tmp_path)
    (tmp_path / "code.py").write_text("x = 1\ny = 2\nz = 3\n")

    res = _edit_file({"path": "code.py", "old_string": "y = 2", "new_string": "y = 42"}, ctx)
    assert not res.is_error
    assert (tmp_path / "code.py").read_text() == "x = 1\ny = 42\nz = 3\n"


def test_edit_file_rejects_missing_match(tmp_path: Path):
    ctx = _ctx(tmp_path)
    (tmp_path / "a.txt").write_text("hello\n")
    res = _edit_file({"path": "a.txt", "old_string": "nope", "new_string": "hi"}, ctx)
    assert res.is_error
    assert "not found" in res.content.lower()


def test_edit_file_rejects_ambiguous_match(tmp_path: Path):
    ctx = _ctx(tmp_path)
    (tmp_path / "a.txt").write_text("TODO\nTODO\n")
    res = _edit_file({"path": "a.txt", "old_string": "TODO", "new_string": "done"}, ctx)
    assert res.is_error
    assert "unique" in res.content.lower() or "2 places" in res.content


def test_edit_file_requires_existing_file(tmp_path: Path):
    ctx = _ctx(tmp_path)
    res = _edit_file({"path": "nope.txt", "old_string": "x", "new_string": "y"}, ctx)
    assert res.is_error


# ----- extract_doc -------------------------------------------------------


def test_extract_doc_handles_plain_text(tmp_path: Path):
    ctx = _ctx(tmp_path)
    (tmp_path / "notes.md").write_text("# Hello\n\nworld")
    res = _extract_doc({"path": "notes.md"}, ctx)
    assert not res.is_error
    assert "Hello" in res.content and "world" in res.content


def test_extract_doc_rejects_missing(tmp_path: Path):
    ctx = _ctx(tmp_path)
    res = _extract_doc({"path": "does-not-exist.pdf"}, ctx)
    assert res.is_error


# ----- computer_use ------------------------------------------------------


from agency.tools import _computer_use


def _computer_ctx(tmp_path: Path, enabled: bool = True) -> ToolContext:
    return ToolContext(workdir=tmp_path.resolve(), allow_computer_use=enabled)


def test_computer_use_off_by_default(tmp_path: Path):
    ctx = _computer_ctx(tmp_path, enabled=False)
    res = _computer_use({"action": "screenshot"}, ctx)
    assert res.is_error
    assert "AGENCY_ENABLE_COMPUTER_USE" in res.content


def test_computer_use_gives_install_hint_when_deps_missing(tmp_path: Path, monkeypatch):
    """With the flag on but pyautogui absent, we should explain what to install."""
    import builtins

    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "pyautogui":
            raise ImportError("no pyautogui here")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", _fake_import)

    ctx = _computer_ctx(tmp_path, enabled=True)
    res = _computer_use({"action": "screenshot"}, ctx)
    assert res.is_error
    assert "pip install" in res.content
    assert "pyautogui" in res.content


def test_computer_use_dispatches_clicks_via_stub(tmp_path: Path, monkeypatch):
    """When pyautogui IS importable, the right function fires for each action."""
    calls: list[tuple] = []

    class _StubAutogui:
        @staticmethod
        def click(*args, **kwargs):
            calls.append(("click", args, kwargs))

        @staticmethod
        def rightClick(*args, **kwargs):
            calls.append(("rightClick", args, kwargs))

        @staticmethod
        def doubleClick(*args, **kwargs):
            calls.append(("doubleClick", args, kwargs))

        @staticmethod
        def write(text, interval=0):
            calls.append(("write", text, interval))

        @staticmethod
        def press(key):
            calls.append(("press", key))

        @staticmethod
        def hotkey(*keys):
            calls.append(("hotkey", keys))

        @staticmethod
        def scroll(amount):
            calls.append(("scroll", amount))

        @staticmethod
        def moveTo(x, y):
            calls.append(("moveTo", x, y))

        @staticmethod
        def position():
            return (100, 200)

    import sys
    monkeypatch.setitem(sys.modules, "pyautogui", _StubAutogui)
    monkeypatch.setitem(sys.modules, "PIL", type("M", (), {})())
    # Pillow's Image submodule is also imported in the handler; stub it.
    pil_image = type("I", (), {})()
    monkeypatch.setattr(sys.modules["PIL"], "Image", pil_image, raising=False)
    monkeypatch.setitem(sys.modules, "PIL.Image", pil_image)

    ctx = _computer_ctx(tmp_path, enabled=True)

    # Click at coordinate
    res = _computer_use({"action": "left_click", "coordinate": [50, 75]}, ctx)
    assert not res.is_error and calls[-1][:2] == ("click", (50, 75))

    # Type text
    res = _computer_use({"action": "type", "text": "hello"}, ctx)
    assert not res.is_error and calls[-1][0] == "write" and calls[-1][1] == "hello"

    # Key chord
    res = _computer_use({"action": "key", "text": "ctrl+c"}, ctx)
    assert not res.is_error and calls[-1] == ("hotkey", ("ctrl", "c"))

    # cursor_position
    res = _computer_use({"action": "cursor_position"}, ctx)
    assert not res.is_error and res.content == "100,200"


def test_computer_use_rejects_unknown_action(tmp_path: Path, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "pyautogui", type("S", (), {})())
    pil_image = type("I", (), {})()
    monkeypatch.setitem(sys.modules, "PIL", type("M", (), {"Image": pil_image})())
    monkeypatch.setitem(sys.modules, "PIL.Image", pil_image)

    ctx = _computer_ctx(tmp_path, enabled=True)
    res = _computer_use({"action": "teleport"}, ctx)
    assert res.is_error
    assert "unsupported action" in res.content.lower()


# ----- SSRF + web_fetch + _truncate -----------------------------------------


def test_is_private_host_blocks_all_private_ranges():
    from agency.tools import _is_private_host
    for host in ["localhost", "127.0.0.1", "10.0.0.1", "192.168.1.1",
                 "172.16.0.1", "169.254.169.254", "::1",
                 "metadata", "metadata.google.internal"]:
        assert _is_private_host(host), f"{host} should be rejected"


def test_web_fetch_refuses_loopback(tmp_path: Path):
    ctx = _ctx(tmp_path)
    ctx.allow_network = True
    from agency.tools import _web_fetch
    res = _web_fetch({"url": "http://127.0.0.1:8080/secret"}, ctx)
    assert res.is_error
    assert "private" in res.content.lower() or "metadata" in res.content.lower() \
        or "loopback" in res.content.lower()


def test_web_fetch_refuses_aws_metadata(tmp_path: Path):
    ctx = _ctx(tmp_path)
    ctx.allow_network = True
    from agency.tools import _web_fetch
    res = _web_fetch({"url": "http://169.254.169.254/latest/meta-data/"}, ctx)
    assert res.is_error


def test_truncate_respects_byte_cap_with_multibyte_text():
    """Even when the input is all multi-byte UTF-8, the encoded result must fit."""
    from agency.tools import _truncate, MAX_OUTPUT_BYTES
    big = "é" * (MAX_OUTPUT_BYTES)  # each 'é' is 2 bytes in UTF-8 → total 2×MAX
    out = _truncate(big)
    assert len(out.encode("utf-8")) <= MAX_OUTPUT_BYTES
    assert "truncated" in out


def test_extract_doc_gives_helpful_hint_when_dep_missing(tmp_path: Path, monkeypatch):
    """If a `.pdf` is requested but pypdf is absent, we should say so — not crash."""
    import builtins

    # Sabotage the import so _extract_pdf raises _MissingDep.
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "pypdf":
            raise ImportError("no pypdf in this env")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", _fake_import)

    (tmp_path / "doc.pdf").write_bytes(b"%PDF-fake")  # content doesn't matter — we fail on import
    ctx = _ctx(tmp_path)
    res = _extract_doc({"path": "doc.pdf"}, ctx)
    assert res.is_error
    assert "pypdf" in res.content
    assert "pip install" in res.content
