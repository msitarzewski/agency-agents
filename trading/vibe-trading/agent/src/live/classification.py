"""Read/write classification for live-channel remote MCP tools.

We do not own the broker's tool names or schemas — they are discovered at
runtime from a server we do not control and are invite-gated, so classification
must be driven by discovery data plus a maintainer-curated map, never a blind
hardcoded name match that silently lets an unrecognized tool through. Every
discovered tool resolves to exactly one of three classes via a strict
precedence ladder (see the live-trading SPEC §7.2):

Tier 1 — MCP tool ``annotations`` (advisory, server-asserted):
    * ``readOnlyHint is True``  → READ
    * ``readOnlyHint is False`` → WRITE (an additive-only order is still a write)
    * ``readOnlyHint is None``  → fall through (absent != read)
Tier 2 — curated per-broker map: an explicit name→class map. **The map wins**
    over annotations whenever it names the tool — a server lying with
    ``readOnlyHint=True`` on its ``place_order`` cannot demote a curated WRITE.
    Annotations can only *catch* writes the map missed, never *excuse* one.
Tier 3 — default-deny: anything neither annotated read-only nor in the map is
    UNKNOWN, handled exactly like WRITE downstream (gate-wrapped, never a plain
    read tool).

The honesty caveat (from ``mcp.types.ToolAnnotations``'s own docstring):
*"Clients should never make tool use decisions based on ToolAnnotations
received from untrusted servers."* So a Tier-1 READ is necessary-but-not-
sufficient to relax safety — it only downgrades toward read, and only when the
curated map has not already pinned the tool WRITE.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from mcp.types import ToolAnnotations


class ToolClass(str, Enum):
    """Read/write classification of a remote MCP tool.

    Attributes:
        READ: Observed to be read-only — wrapped as a plain ``MCPRemoteTool``.
        WRITE: Mutates broker state (order placement/cancel) — gate-wrapped.
        UNKNOWN: Unrecognized — fail-closed, treated identically to WRITE.
    """

    READ = "read"
    WRITE = "write"
    UNKNOWN = "unknown"


def classify_tool(
    name: str,
    annotations: "ToolAnnotations | None",
    curated: Mapping[str, ToolClass] | None = None,
) -> ToolClass:
    """Classify one remote tool via the 3-tier precedence ladder.

    The curated map is authoritative: when it names the tool, its class is
    returned regardless of any annotation (a deceptive ``readOnlyHint`` cannot
    override a curated WRITE). Otherwise an explicit ``readOnlyHint`` decides;
    an absent hint is NOT treated as read. Anything left over is UNKNOWN.

    Args:
        name: Remote tool name (the broker's un-prefixed name).
        annotations: The tool's ``mcp.types.ToolAnnotations``, or ``None`` when
            the server provided none.
        curated: Per-broker name→:class:`ToolClass` map (Tier 2). When omitted,
            only Tiers 1 and 3 apply (so an annotation-less tool is UNKNOWN).

    Returns:
        The resolved :class:`ToolClass`.
    """
    # Tier 2 wins whenever the map names the tool.
    if curated is not None:
        pinned = curated.get(name)
        if pinned is not None:
            return pinned

    # Tier 1: explicit annotation. Absent (None) hint falls through.
    if annotations is not None:
        hint = getattr(annotations, "readOnlyHint", None)
        if hint is True:
            return ToolClass.READ
        if hint is False:
            return ToolClass.WRITE

    # Tier 3: default-deny.
    return ToolClass.UNKNOWN
