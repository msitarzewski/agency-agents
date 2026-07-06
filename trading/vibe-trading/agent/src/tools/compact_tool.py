"""Compact tool: model-initiated context compression."""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool


class CompactTool(BaseTool):
    """Compress conversation history to free context space."""

    name = "compact"
    description = "Compress conversation history to free context space. Call when the conversation feels long or you're losing track of earlier context. Optionally specify focus_topic to preserve details about a specific subject."
    parameters = {
        "type": "object",
        "properties": {
            "focus_topic": {"type": "string", "description": "Topic to preserve in detail during compression (e.g. 'BTC-USDT backtest')"},
        },
        "required": [],
    }
    is_readonly = False

    def execute(self, **kwargs: Any) -> str:
        return json.dumps({"status": "ok", "message": "Compression triggered"})
