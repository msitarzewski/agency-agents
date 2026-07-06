"""Reusable CLI render components.

Each component returns a Rich renderable (Text / Panel / Table) so callers
can ``console.print`` or stuff it into a Live group.
"""

from .chat_log import render_history
from .hint_bar import render_hint_bar
from .tool_event import render_tool_event, render_tool_events
from .working_indicator import ThinkingSpinner

__all__ = [
    "ThinkingSpinner",
    "render_history",
    "render_hint_bar",
    "render_tool_event",
    "render_tool_events",
]
