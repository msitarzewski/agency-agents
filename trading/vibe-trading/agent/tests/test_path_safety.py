"""Tests for path safety helpers in src.tools.path_utils."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.path_utils import safe_document_path, safe_path, safe_run_dir, safe_run_id, safe_user_path


# ---------------------------------------------------------------------------
# safe_path — tool-controlled sandbox under a fixed workdir
# ---------------------------------------------------------------------------

class TestSafePath:
    def test_relative_path_resolves_under_workdir(self, tmp_path: Path):
        result = safe_path("notes.md", tmp_path)
        assert result == (tmp_path / "notes.md").resolve()

    def test_nested_relative_path_ok(self, tmp_path: Path):
        result = safe_path("sub/dir/file.txt", tmp_path)
        assert result == (tmp_path / "sub" / "dir" / "file.txt").resolve()

    def test_parent_traversal_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="escapes the workspace"):
            safe_path("../../etc/passwd", tmp_path)

    def test_absolute_path_outside_workdir_rejected(self, tmp_path: Path):
        outside = tmp_path.parent / "elsewhere.txt"
        with pytest.raises(ValueError, match="escapes the workspace"):
            safe_path(str(outside), tmp_path)

    def test_unc_path_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="UNC paths"):
            safe_path("\\\\server\\share\\evil.csv", tmp_path)

    def test_unix_double_slash_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="UNC paths"):
            safe_path("//server/share/evil.csv", tmp_path)

    def test_normalizes_redundant_segments(self, tmp_path: Path):
        (tmp_path / "a").mkdir()
        result = safe_path("a/./file.txt", tmp_path)
        assert result == (tmp_path / "a" / "file.txt").resolve()


# ---------------------------------------------------------------------------
# safe_user_path — user-supplied broker files under explicit import roots
# ---------------------------------------------------------------------------

class TestSafeUserPath:
    def test_configured_import_root_file_accepted(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
        target = tmp_path / "broker.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()

        result = safe_user_path(str(target))
        assert result == target.resolve()

    def test_tilde_expansion_works(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", "~/.vibe-imports")
        target = tmp_path / ".vibe-imports" / "journal.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()

        result = safe_user_path("~/.vibe-imports/journal.csv")
        assert result == target.resolve()

    def test_default_cwd_uploads_file_accepted(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        target = tmp_path / "uploads" / "local.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        result = safe_user_path(str(target))
        assert result == target.resolve()

    def test_system_path_outside_import_roots_rejected(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="outside allowed user-file roots"):
            safe_user_path("/etc/passwd")

    def test_parent_traversal_from_cwd_rejected(self, tmp_path: Path, monkeypatch):
        deep = tmp_path / "deep" / "cwd"
        deep.mkdir(parents=True)
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(deep))
        monkeypatch.chdir(deep)

        with pytest.raises(ValueError, match="outside allowed user-file roots"):
            safe_user_path("../../../../../etc/passwd")

    def test_unc_path_rejected(self):
        with pytest.raises(ValueError, match="UNC paths"):
            safe_user_path("\\\\evil-server\\share\\passwd.csv")

    def test_unix_double_slash_rejected(self):
        with pytest.raises(ValueError, match="UNC paths"):
            safe_user_path("//evil-server/share/passwd.csv")


class TestSafeDocumentPath:
    def test_upload_handle_resolves_to_agent_uploads(self) -> None:
        result = safe_document_path("uploads/local.csv")

        assert result == (Path(__file__).resolve().parents[1] / "uploads" / "local.csv").resolve()

    def test_upload_handle_traversal_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="outside allowed document roots"):
            safe_document_path("uploads/../api_server.py")


# ---------------------------------------------------------------------------
# safe_run_dir — tool/backtest run roots
# ---------------------------------------------------------------------------

class TestSafeRunDir:
    def test_configured_run_root_accepted(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))
        run_dir = tmp_path / "run_123"
        run_dir.mkdir()

        result = safe_run_dir(str(run_dir))

        assert result == run_dir.resolve()

    def test_system_tmp_run_dir_rejected_by_default(self, tmp_path: Path, monkeypatch):
        monkeypatch.delenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", raising=False)
        run_dir = tmp_path / "attack_run"
        run_dir.mkdir()

        with pytest.raises(ValueError, match="outside allowed run roots"):
            safe_run_dir(str(run_dir))

    def test_default_agent_runs_dir_accepted(self, tmp_path: Path, monkeypatch):
        monkeypatch.delenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", raising=False)
        agent_runs = Path(__file__).resolve().parents[1] / "runs" / "safe_run"
        agent_runs.mkdir(parents=True, exist_ok=True)

        result = safe_run_dir(str(agent_runs))

        assert result == agent_runs.resolve()


class TestSafeRunId:
    def test_configured_run_id_accepted(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))
        run_dir = tmp_path / "run_123"
        run_dir.mkdir()

        result = safe_run_id("run_123")

        assert result == run_dir.resolve()

    def test_path_shaped_run_id_rejected(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))

        with pytest.raises(ValueError, match="bare run directory name"):
            safe_run_id("../api_server.py")

    def test_missing_run_id_rejected(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))

        with pytest.raises(ValueError, match="was not found"):
            safe_run_id("missing_run")
