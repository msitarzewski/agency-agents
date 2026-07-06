"""Session search tool: FTS5 cross-session search for past conversations."""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool


class SessionSearchTool(BaseTool):
    """Search past conversation sessions by keyword using SQLite FTS5."""

    name = "session_search"
    description = (
        "Search past conversation sessions by keyword. Returns matching sessions "
        "with context snippets. Use when the user references past work, previous "
        "strategies, or earlier conversations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (keywords or phrase)",
            },
            "max_results": {
                "type": "integer",
                "description": "Max sessions to return (default 3, max 10)",
                "default": 3,
            },
        },
        "required": ["query"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Search past sessions.

        Args:
            **kwargs: Must include query; optionally max_results.

        Returns:
            JSON with search results or error.
        """
        query = kwargs.get("query", "")
        if not query:
            return json.dumps({"status": "error", "error": "query required"})

        max_results = min(int(kwargs.get("max_results", 3)), 10)

        try:
            from src.session.search import get_shared_index
            matches = get_shared_index().search(query, max_sessions=max_results)

            if not matches:
                return json.dumps(
                    {"status": "ok", "message": f"No past sessions matching '{query}'", "results": []},
                    ensure_ascii=False,
                )

            return json.dumps(
                {"status": "ok", "query": query, "results": [m.to_dict() for m in matches]},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
