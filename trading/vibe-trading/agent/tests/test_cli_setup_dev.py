"""Unit tests for the cross-platform `vibe-trading setup` and
`vibe-trading dev` commands.

These tests cover the entrypoint and platform-aware build-command
selection. They do not actually invoke ``npm`` (we mock ``shutil.which``
and ``subprocess.run``), so they run in any environment.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import cli


class TestIsWindows:
    def test_true_on_win32(self) -> None:
        with patch.object(cli._legacy.sys, "platform", "win32"):
            assert cli._legacy._is_windows() is True

    def test_false_on_linux(self) -> None:
        with patch.object(cli._legacy.sys, "platform", "linux"):
            assert cli._legacy._is_windows() is False

    def test_false_on_darwin(self) -> None:
        with patch.object(cli._legacy.sys, "platform", "darwin"):
            assert cli._legacy._is_windows() is False


class TestBuildFrontendCmd:
    """The Windows sequence must use ``npm exec --package=...`` to avoid
    npx pulling the abandoned ``tsc@2.0.4`` package from the registry."""

    def test_windows_pins_typescript_and_vite_packages(self) -> None:
        with patch.object(cli._legacy.sys, "platform", "win32"):
            steps = cli._legacy._build_frontend_cmd(Path("frontend"))
        # First step is always `npm install`.
        assert steps[0][:1] == ["npm"]
        assert steps[0][1] == "install"
        # Subsequent steps must pin --package= so npx/npm exec cannot
        # accidentally fetch the abandoned `tsc` package.
        assert any(
            "--package=typescript" in step and "tsc" in step for step in steps[1:]
        ), f"expected an explicit typescript pin, got: {steps[1:]}"
        assert any(
            "--package=vite" in step and "vite" in step and "build" in step
            for step in steps[1:]
        ), f"expected an explicit vite build pin, got: {steps[1:]}"

    def test_posix_uses_npm_run_build(self) -> None:
        with patch.object(cli._legacy.sys, "platform", "linux"):
            steps = cli._legacy._build_frontend_cmd(Path("frontend"))
        assert steps[-1] == ["npm", "run", "build"]

    def test_posix_does_not_pin_packages(self) -> None:
        """On POSIX, npm's local PATH magic makes ``npm run build`` work
        without explicit package pinning. Keep it that way."""
        with patch.object(cli._legacy.sys, "platform", "linux"):
            steps = cli._legacy._build_frontend_cmd(Path("frontend"))
        for step in steps:
            assert "--package=" not in step, f"unexpected pin on POSIX: {step}"


class TestCmdSetupNodeMissing:
    """When node or npm is not on PATH we should fail fast with a clear
    message and the USAGE exit code, instead of letting the user see a
    raw ENOENT from npm."""

    def test_fails_when_node_missing(self, tmp_path: Path, capsys) -> None:
        # Build a fake frontend dir so the directory check passes.
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()

        with patch.object(cli._legacy, "_resolve_node_and_npm", return_value=(None, "/usr/bin/npm")):
            rc = cli._legacy.cmd_setup(frontend_dir=frontend_dir)
        assert rc == cli._legacy.EXIT_USAGE_ERROR
        out = capsys.readouterr().out
        assert "node" in out

    def test_fails_when_npm_missing(self, tmp_path: Path, capsys) -> None:
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()

        with patch.object(cli._legacy, "_resolve_node_and_npm", return_value=("/usr/bin/node", None)):
            rc = cli._legacy.cmd_setup(frontend_dir=frontend_dir)
        assert rc == cli._legacy.EXIT_USAGE_ERROR
        out = capsys.readouterr().out
        assert "npm" in out

    def test_fails_when_frontend_dir_missing(self, tmp_path: Path, capsys) -> None:
        missing = tmp_path / "no-such-frontend"
        with patch.object(cli._legacy, "_resolve_node_and_npm", return_value=("/usr/bin/node", "/usr/bin/npm")):
            rc = cli._legacy.cmd_setup(frontend_dir=missing)
        assert rc == cli._legacy.EXIT_USAGE_ERROR
        out = capsys.readouterr().out
        assert "not found" in out.lower() or "not on PATH" in out


class TestCmdSetupRunsSteps:
    """When Node and the frontend dir are present, cmd_setup should
    invoke the right number of steps in order and return success."""

    def test_runs_all_steps(self, tmp_path: Path) -> None:
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "dist").mkdir()  # simulate a build output

        with patch.object(cli._legacy, "_resolve_node_and_npm", return_value=("/usr/bin/node", "/usr/bin/npm")):
            with patch.object(cli._legacy, "_is_windows", return_value=False):
                with patch("cli._legacy.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    rc = cli._legacy.cmd_setup(frontend_dir=frontend_dir)

        assert rc == cli._legacy.EXIT_SUCCESS
        # On POSIX: exactly 2 steps (install + run build).
        assert mock_run.call_count == 2
        # The last invocation should be `npm run build`.
        last_cmd = mock_run.call_args_list[-1].args[0]
        assert last_cmd[:3] == ["npm", "run", "build"]

    def test_returns_run_failed_when_step_fails(self, tmp_path: Path) -> None:
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()

        with patch.object(cli._legacy, "_resolve_node_and_npm", return_value=("/usr/bin/node", "/usr/bin/npm")):
            with patch.object(cli._legacy, "_is_windows", return_value=False):
                with patch("cli._legacy.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1, stdout="", stderr="boom: failed"
                    )
                    rc = cli._legacy.cmd_setup(frontend_dir=frontend_dir)

        assert rc == cli._legacy.EXIT_RUN_FAILED
        # Should bail out on the first failing step, not run them all.
        assert mock_run.call_count == 1


class TestCmdDev:
    """`vibe-trading dev` should use vite.config.ts's port (5899), not
    5173, and launch the backend from AGENT_DIR so the in-repo `cli`
    package is importable."""

    def test_default_frontend_port_is_5899(self) -> None:
        """Hardcoded wrong-port regression: this is the value users see
        in the banner. Vite config sets 5899; we must not print 5173."""
        # We don't actually run the command (it never returns), just
        # inspect the documented default by calling the function with
        # patched subprocess that raises immediately.
        with patch("cli._legacy._resolve_node_and_npm", return_value=("/usr/bin/node", "/usr/bin/npm")):
            with patch("cli._legacy.subprocess.Popen") as mock_popen:
                # Both children "exit" immediately so the wait loop ends.
                proc = MagicMock()
                proc.poll.return_value = 0
                mock_popen.return_value = proc
                with patch.object(cli._legacy.time, "sleep", side_effect=KeyboardInterrupt):
                    rc = cli._legacy.cmd_dev()

        # First Popen call: backend. Second: frontend.
        backend_call = mock_popen.call_args_list[0]
        frontend_call = mock_popen.call_args_list[1]
        backend_cmd = backend_call.args[0]
        frontend_cmd = frontend_call.args[0]
        # Backend must run from AGENT_DIR, not the repo root.
        assert backend_call.kwargs.get("cwd") == str(cli._legacy.AGENT_DIR)
        # Backend invocation must be `python -m cli._legacy serve`.
        assert backend_cmd[:4] == [sys.executable, "-m", "cli._legacy", "serve"]
        # Frontend invocation must pass the configured vite port (5899 by
        # default; --port 5173 would be a bug).
        assert "--port" in frontend_cmd
        port_idx = frontend_cmd.index("--port") + 1
        assert frontend_cmd[port_idx] == "5899", (
            f"dev printed wrong frontend port; got {frontend_cmd[port_idx]!r}, expected '5899'"
        )
        # Process should have returned cleanly.
        assert rc == cli._legacy.EXIT_SUCCESS

    def test_custom_frontend_port_propagates(self, tmp_path: Path) -> None:
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        with patch("cli._legacy._resolve_node_and_npm", return_value=("/usr/bin/node", "/usr/bin/npm")):
            with patch("cli._legacy.subprocess.Popen") as mock_popen:
                proc = MagicMock()
                proc.poll.return_value = 0
                mock_popen.return_value = proc
                with patch.object(cli._legacy.time, "sleep", side_effect=KeyboardInterrupt):
                    cli._legacy.cmd_dev(frontend_port=6000, frontend_dir=frontend_dir)

        frontend_call = mock_popen.call_args_list[1]
        frontend_cmd = frontend_call.args[0]
        port_idx = frontend_cmd.index("--port") + 1
        assert frontend_cmd[port_idx] == "6000"
