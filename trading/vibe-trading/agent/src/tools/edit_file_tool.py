"""Edit file tool: find-and-replace in workspace files."""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool
from src.tools.path_utils import allowed_write_roots
from src.tools.path_utils import resolve_safe_path
from src.tools.redaction import redact_internal_paths


class EditFileTool(BaseTool):
    """Find and replace the first occurrence of a string in a workspace file."""

    name = "edit_file"
    description = "Find and replace the first occurrence of old_text with new_text in a file."
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path relative to run_dir"},
            "old_text": {"type": "string", "description": "Text to find"},
            "new_text": {"type": "string", "description": "Text to replace with"},
        },
        "required": ["path", "old_text", "new_text"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Perform find-and-replace.

        Args:
            **kwargs: Must include path, old_text, new_text. Optional run_dir.

        Returns:
            JSON string with the operation result or an error.
        """
        file_path = kwargs["path"]
        old_text = kwargs["old_text"]
        new_text = kwargs["new_text"]
        run_dir = kwargs.get("run_dir")

        try:
            resolved = resolve_safe_path(
                file_path=file_path,
                run_dir=run_dir,
                allowed_roots=allowed_write_roots(),
                purpose="write",
            )
        except ValueError as exc:
            return json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                },
                ensure_ascii=False,
            )

        if not resolved.exists():
            return json.dumps(
                {
                    "status": "error",
                    "error": f"File not found: {file_path}",
                },
                ensure_ascii=False,
            )

        try:
            content = resolved.read_text(encoding="utf-8")
            if old_text not in content:
                return json.dumps(
                    {
                        "status": "error",
                        "error": f"old_text not found in {file_path}",
                    },
                    ensure_ascii=False,
                )
            new_content = content.replace(old_text, new_text, 1)
            resolved.write_text(new_content, encoding="utf-8")
            return json.dumps(
                {
                    "status": "ok",
                    "path": str(resolved),
                    "message": "Edit applied successfully",
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
