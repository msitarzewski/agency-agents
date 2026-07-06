"""Read file tool: read file contents from the workspace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agent.tools import BaseTool
from src.tools.path_utils import safe_path as _safe_path
from src.tools.path_utils import safe_run_dir as _safe_run_dir
from src.tools.path_utils import allowed_file_roots
from src.tools.redaction import redact_internal_paths

_OUTPUT_LIMIT = 50_000


class ReadFileTool(BaseTool):
    """Read file contents with optional line limit."""

    name = "read_file"
    description = "Read a file from the workspace. Returns file contents with optional line limit."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path relative to run_dir or skills/"},
            "limit": {"type": "integer", "description": "Max number of lines to return (default: all)"},
        },
        "required": ["path"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Read a file.

        Args:
            **kwargs: Must include path. Optional limit and run_dir.

        Returns:
            JSON string containing content or an error.
        """
        file_path = kwargs["path"]
        limit = kwargs.get("limit")
        run_dir = kwargs.get("run_dir")

        allowed_roots = []
        if run_dir:
            try:
                allowed_roots.append(_safe_run_dir(str(run_dir)))
            except ValueError as exc:
                return json.dumps(
                    {
                        "status": "error",
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
        # Read-only access to skills/
        skills_dir = Path(__file__).resolve().parents[1] / "skills"
        if skills_dir.exists():
            allowed_roots.append(skills_dir.resolve())

        # Add configured extra file roots (VIBE_TRADING_ALLOWED_FILE_ROOTS)
        for extra_root in allowed_file_roots():
            if extra_root not in allowed_roots:
                allowed_roots.append(extra_root)

        # Strip redundant "skills/" prefix that LLMs sometimes add
        paths_to_try = [file_path]
        if file_path.startswith("skills/"):
            paths_to_try.append(file_path[len("skills/") :])

        resolved = None
        for root in allowed_roots:
            for p in paths_to_try:
                try:
                    candidate = _safe_path(p, root)
                    if candidate.exists():
                        resolved = candidate
                        break
                except ValueError:
                    continue
            if resolved:
                break

        if resolved is None:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"File not found or path escapes workspace: {file_path}",
                },
                ensure_ascii=False,
            )

        try:
            text = resolved.read_text(encoding="utf-8")
            if limit and limit > 0:
                lines = text.splitlines(keepends=True)
                text = "".join(lines[:limit])
            if len(text) > _OUTPUT_LIMIT:
                text = text[:_OUTPUT_LIMIT] + "\n... (truncated)"
            return json.dumps(
                {
                    "status": "ok",
                    "path": str(resolved),
                    "content": text,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps(
                {
                    "status": "error",
                    "error": redact_internal_paths(str(exc)),
                },
                ensure_ascii=False,
            )
