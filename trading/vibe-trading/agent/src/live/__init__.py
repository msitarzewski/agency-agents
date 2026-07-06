"""Live trading channel (Robinhood Agentic Trading).

Bounded-autonomy live execution: the agent trades autonomously inside a
user-committed mandate, on funds ring-fenced in the broker's dedicated
agentic account, with an out-of-band kill switch and a full audit trail.

All live-channel state lives under ``~/.vibe-trading/live/`` (see
:mod:`src.live.paths`). The mandate is read-only at the agent loop — there is
no write path reachable from a tool (see the live-trading SPEC §3).
"""
